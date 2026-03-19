"""
Script de chargement initial des données historiques Olist dans PostgreSQL.
Couche RAW : données brutes, aucune transformation.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# --- Configuration de la connexion ---
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ecommerce_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Mapping fichier CSV → nom de table en base ---
CSV_TABLE_MAP = {
    "olist_orders_dataset.csv":          "raw_orders",
    "olist_order_items_dataset.csv":     "raw_order_items",
    "olist_order_payments_dataset.csv":  "raw_order_payments",
    "olist_order_reviews_dataset.csv":   "raw_order_reviews",
    "olist_customers_dataset.csv":       "raw_customers",
    "olist_products_dataset.csv":        "raw_products",
    "olist_sellers_dataset.csv":         "raw_sellers",
    "product_category_name_translation.csv": "raw_product_category_translation",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def create_raw_schema(engine):
    """Crée le schéma 'raw' dans PostgreSQL s'il n'existe pas."""
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()
    print("[OK] Schema 'raw' prêt.")


def load_csv_to_postgres(engine, csv_filename, table_name):
    """Charge un CSV dans la table raw.{table_name}."""
    filepath = os.path.join(DATA_DIR, csv_filename)

    if not os.path.exists(filepath):
        print(f"[SKIP] Fichier introuvable : {csv_filename}")
        return

    print(f"[LOAD] {csv_filename} → raw.{table_name} ...", end=" ")
    df = pd.read_csv(filepath)

    df.to_sql(
        name=table_name,
        schema="raw",
        con=engine,
        if_exists="replace",   # Remplace si la table existe déjà
        index=False,
        method="multi",        # Insère par lots (plus rapide)
        chunksize=1000,
    )
    print(f"{len(df):,} lignes chargées.")


def main():
    print("=== Chargement des données historiques Olist ===\n")

    # Connexion à PostgreSQL
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Connexion PostgreSQL établie.\n")
    except Exception as e:
        print(f"[ERREUR] Impossible de se connecter à PostgreSQL :\n{e}")
        print("\nVérifie que :")
        print("  - PostgreSQL est bien démarré")
        print("  - Ton fichier .env est correct (host, port, password)")
        return

    # Création du schéma raw
    create_raw_schema(engine)

    # Chargement de chaque CSV
    for csv_file, table_name in CSV_TABLE_MAP.items():
        load_csv_to_postgres(engine, csv_file, table_name)

    print("\n=== Chargement terminé ! ===")
    print("Tu peux vérifier dans pgAdmin : schéma 'raw', 8 tables.")


if __name__ == "__main__":
    main()
