"""
DAG : ecommerce_etl_pipeline
Description : Pipeline ETL complet pour la plateforme e-commerce
              - Extract  : appel API pour générer une nouvelle commande
              - Transform: mise à jour de la couche clean
              - Load     : mise à jour de la couche analytics

Fréquence : toutes les 15 minutes
"""

from datetime import datetime, timedelta
import os
import requests
import psycopg2

from airflow import DAG
from airflow.operators.python import PythonOperator

# ─────────────────────────────────────────
# Configuration base de données
# ─────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("ECOMMERCE_DB_HOST", "host.docker.internal"),
    "port":     os.environ.get("ECOMMERCE_DB_PORT", "5434"),
    "dbname":   os.environ.get("ECOMMERCE_DB_NAME", "ecommerce_db"),
    "user":     os.environ.get("ECOMMERCE_DB_USER", "postgres"),
    "password": os.environ.get("ECOMMERCE_DB_PASSWORD", ""),
}

API_URL = os.environ.get("ECOMMERCE_API_URL", "http://host.docker.internal:8000")

# ─────────────────────────────────────────
# Fonctions des tâches
# ─────────────────────────────────────────

def update_order_statuses(**context):
    """
    Met à jour les statuts des commandes en attente AVANT de générer de nouvelles commandes.
    - processing → shipped   (après 15 min réelles)
    - shipped    → delivered (après 45 min réelles)
    Les commandes delivered apparaîtront dans les KPIs analytics.
    """
    url = f"{API_URL}/orders/update-statuses"
    response = requests.post(url, timeout=10)

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    data = response.json()
    print(f"[STATUS UPDATE] {data['message']}")
    return data


def extract_new_order(**context):
    """
    Appelle l'API FastAPI pour générer un batch de commandes selon la saisonnalité.
    Volume : ~10 commandes/run en normale, jusqu'à ~15 en novembre (Black Friday).
    """
    url = f"{API_URL}/orders/batch"
    response = requests.post(url, timeout=30)

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    data = response.json()
    n = data.get("orders_generated", 0)
    factor = data.get("seasonality_factor", 1.0)
    print(f"[EXTRACT] {n} commandes insérées (facteur saisonnalité : {factor})")

    context["ti"].xcom_push(key="orders_generated", value=n)
    return n


def transform_clean_layer(**context):
    """
    Rafraîchit les tables de la couche clean.
    On recrée uniquement les tables impactées pour être efficace.
    """
    order_id = context["ti"].xcom_pull(key="order_id", task_ids="extract")
    print(f"[TRANSFORM] Mise à jour couche clean pour order_id={order_id}")

    # On exécute les scripts SQL du dossier /opt/airflow/sql/clean/
    sql_dir = "/opt/airflow/sql/clean"
    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()

    for sql_file in sql_files:
        path = os.path.join(sql_dir, sql_file)
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
        print(f"  → {sql_file}")
        cursor.execute(sql)

    cursor.close()
    conn.close()
    print("[TRANSFORM] Couche clean mise à jour.")


def load_analytics_layer(**context):
    """
    Rafraîchit les tables de la couche analytics (KPIs).
    """
    order_id = context["ti"].xcom_pull(key="order_id", task_ids="extract")
    print(f"[LOAD] Mise à jour couche analytics pour order_id={order_id}")

    sql_dir = "/opt/airflow/sql/analytics"
    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()

    for sql_file in sql_files:
        path = os.path.join(sql_dir, sql_file)
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
        print(f"  → {sql_file}")
        cursor.execute(sql)

    cursor.close()
    conn.close()
    print("[LOAD] Couche analytics mise à jour.")


def check_data_quality(**context):
    """
    Vérifie la qualité des données après insertion.
    Contrôles basiques : pas de NULLs critiques, cohérence des montants.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    checks = {
        "Commandes sans customer_id": """
            SELECT COUNT(*) FROM raw.raw_orders
            WHERE customer_id IS NULL
        """,
        "Paiements avec montant nul": """
            SELECT COUNT(*) FROM raw.raw_order_payments
            WHERE payment_value <= 0
        """,
        "Commandes orphelines (sans paiement)": """
            SELECT COUNT(*) FROM raw.raw_orders o
            LEFT JOIN raw.raw_order_payments p ON o.order_id = p.order_id
            WHERE p.order_id IS NULL
              AND o.order_status = 'delivered'
        """,
    }

    issues = []
    for label, query in checks.items():
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"  [{label}] : {count}")
        if count > 0:
            issues.append(f"{label}: {count} lignes problématiques")

    cursor.close()
    conn.close()

    if issues:
        print(f"[WARNING] Problèmes détectés : {issues}")
    else:
        print("[DATA QUALITY] Tous les contrôles passés.")


# ─────────────────────────────────────────
# Définition du DAG
# ─────────────────────────────────────────

default_args = {
    "owner": "ecommerce_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}

with DAG(
    dag_id="ecommerce_etl_pipeline",
    description="Pipeline ETL temps réel e-commerce",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/15 * * * *",   # toutes les 15 minutes
    catchup=False,
    tags=["ecommerce", "etl", "production"],
) as dag:

    t_update_statuses = PythonOperator(
        task_id="update_statuses",
        python_callable=update_order_statuses,
    )

    t_extract = PythonOperator(
        task_id="extract",
        python_callable=extract_new_order,
    )

    t_transform = PythonOperator(
        task_id="transform",
        python_callable=transform_clean_layer,
    )

    t_load = PythonOperator(
        task_id="load",
        python_callable=load_analytics_layer,
    )

    t_quality = PythonOperator(
        task_id="data_quality_check",
        python_callable=check_data_quality,
    )

    # Ordre d'exécution : Update Statuses → Extract → Transform → Load → Quality Check
    t_update_statuses >> t_extract >> t_transform >> t_load >> t_quality
