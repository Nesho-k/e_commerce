"""
ETL PySpark — Chargement des données Olist dans PostgreSQL
Remplace le pipeline Pandas de load_historical_data.py pour simuler
un traitement distribué sur les 100K+ commandes et 94K+ clients.
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)


def run_spark_etl():
    print("=== Pipeline ETL PySpark — Olist E-commerce ===\n")

    # Initialisation de la session Spark en mode local (tous les cœurs disponibles)
    spark = SparkSession.builder \
        .appName("EcommerceETL") \
        .master("local[*]") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.commit()

    # --- EXTRACT : lecture des CSV avec PySpark ---
    print("[EXTRACT] Lecture des fichiers CSV ...\n")

    orders = spark.read.csv(f"{DATA_DIR}/olist_orders_dataset.csv", header=True, inferSchema=True)
    customers = spark.read.csv(f"{DATA_DIR}/olist_customers_dataset.csv", header=True, inferSchema=True)
    payments = spark.read.csv(f"{DATA_DIR}/olist_order_payments_dataset.csv", header=True, inferSchema=True)
    items = spark.read.csv(f"{DATA_DIR}/olist_order_items_dataset.csv", header=True, inferSchema=True)
    reviews = spark.read.csv(f"{DATA_DIR}/olist_order_reviews_dataset.csv", header=True, inferSchema=True)
    products = spark.read.csv(f"{DATA_DIR}/olist_products_dataset.csv", header=True, inferSchema=True)
    sellers = spark.read.csv(f"{DATA_DIR}/olist_sellers_dataset.csv", header=True, inferSchema=True)
    categories = spark.read.csv(f"{DATA_DIR}/product_category_name_translation.csv", header=True, inferSchema=True)

    print(f"  orders    : {orders.count():,} lignes")
    print(f"  customers : {customers.count():,} lignes")
    print(f"  payments  : {payments.count():,} lignes")
    print(f"  items     : {items.count():,} lignes")

    # --- TRANSFORM : nettoyage de base avec PySpark ---
    print("\n[TRANSFORM] Nettoyage et preprocessing ...\n")

    # Suppression des doublons et des lignes avec des colonnes clés nulles
    orders = orders.dropDuplicates(["order_id"]).filter(F.col("order_id").isNotNull())
    customers = customers.dropDuplicates(["customer_id"]).filter(F.col("customer_unique_id").isNotNull())
    payments = payments.filter(F.col("payment_value") > 0)

    # Agrégation des paiements par commande (plusieurs lignes possibles par order_id)
    payments_agg = payments.groupBy("order_id").agg(
        F.sum("payment_value").alias("total_payment")
    )

    # Agrégation des items par commande
    items_agg = items.groupBy("order_id").agg(
        F.count("order_item_id").alias("item_count"),
        F.sum("price").alias("total_price")
    )

    print(f"  Commandes après déduplication : {orders.count():,}")

    # --- LOAD : écriture dans PostgreSQL via .toPandas() ---
    # scikit-learn et SQLAlchemy ne supportent pas les DataFrames Spark directement
    print("\n[LOAD] Écriture dans PostgreSQL ...\n")

    datasets = [
        (orders,        "raw_orders"),
        (customers,     "raw_customers"),
        (payments_agg,  "raw_order_payments"),
        (items_agg,     "raw_order_items"),
        (reviews,       "raw_order_reviews"),
        (products,      "raw_products"),
        (sellers,       "raw_sellers"),
        (categories,    "raw_product_category_translation"),
    ]

    for df_spark, table_name in datasets:
        df_pandas = df_spark.toPandas()
        print(f"  [LOAD] raw.{table_name} — {len(df_pandas):,} lignes ...", end=" ")
        df_pandas.to_sql(
            name=table_name,
            schema="raw",
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=1000,
        )
        print("OK")

    spark.stop()
    print("\n=== ETL PySpark terminé ===")


if __name__ == "__main__":
    run_spark_etl()
