"""
DAG : rfm_segmentation_pipeline
Description : Segmentation client RFM avec K-Means
              - Calcule les features Recency, Frequency, Monetary
              - Entraîne un K-Means (4 clusters)
              - Loggue les métriques dans MLflow
              - Sauvegarde les segments dans analytics.customer_segments

Fréquence : tous les jours à 2h du matin
"""

from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator


def run_rfm_segmentation(**context):
    """
    Lance la segmentation RFM complète.
    Importe le script depuis /opt/airflow/scripts.
    """
    sys.path.insert(0, "/opt/airflow/scripts")
    from rfm_segmentation import run_segmentation

    silhouette = run_segmentation()
    print(f"[DAG RFM] Segmentation terminée — silhouette : {silhouette:.3f}")
    context["ti"].xcom_push(key="silhouette_score", value=round(silhouette, 4))


# ─────────────────────────────────────────
# Définition du DAG
# ─────────────────────────────────────────

default_args = {
    "owner": "ecommerce_team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="rfm_segmentation_pipeline",
    description="Segmentation client RFM + K-Means + MLflow (quotidien)",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 2 * * *",   # tous les jours à 2h
    catchup=False,
    tags=["ecommerce", "ml", "rfm", "segmentation"],
) as dag:

    t_rfm = PythonOperator(
        task_id="rfm_segmentation",
        python_callable=run_rfm_segmentation,
    )

    t_rfm
