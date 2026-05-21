"""
RFM Segmentation avec K-Means
Calcule les scores Recency, Frequency, Monetary par client
et applique un clustering K-Means pour segmenter les clients.
Les résultats sont trackés avec MLflow et sauvegardés dans analytics.customer_segments.
"""

import os
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import mlflow
import mlflow.sklearn
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)


def compute_rfm_spark():
    """Calcule les features RFM par client avec PySpark, puis convertit en Pandas pour scikit-learn."""

    spark = SparkSession.builder \
        .appName("RFM_Segmentation") \
        .master("local[*]") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Lecture des CSV avec PySpark (traitement distribué)
    orders = spark.read.csv(f"{DATA_DIR}/olist_orders_dataset.csv", header=True, inferSchema=True)
    customers = spark.read.csv(f"{DATA_DIR}/olist_customers_dataset.csv", header=True, inferSchema=True)
    payments = spark.read.csv(f"{DATA_DIR}/olist_order_payments_dataset.csv", header=True, inferSchema=True)

    # On garde uniquement les commandes livrées
    orders = orders.filter(F.col("order_status") == "delivered")

    # Agrégation des paiements par commande (une commande peut avoir plusieurs paiements)
    payments_agg = payments.groupBy("order_id").agg(
        F.sum("payment_value").alias("total_payment")
    )

    # Jointures pour regrouper clients, commandes et paiements
    df = customers.join(orders, "customer_id").join(payments_agg, "order_id")

    # Date de référence pour calculer la recency
    reference_date = df.select(F.max("order_purchase_timestamp")).collect()[0][0]

    # Calcul des métriques RFM par client avec groupBy Spark
    rfm = df.groupBy("customer_unique_id").agg(
        F.max("order_purchase_timestamp").alias("last_order_date"),
        F.countDistinct("order_id").alias("frequency"),
        F.sum("total_payment").alias("monetary")
    )

    rfm = rfm.withColumn("recency", F.datediff(F.lit(reference_date), F.col("last_order_date")))
    rfm = rfm.select("customer_unique_id", "recency", "frequency", "monetary").dropna()

    print(f"[SPARK] {rfm.count():,} clients traités")

    # Conversion en Pandas : scikit-learn ne prend pas de DataFrame Spark en entrée
    df_pandas = rfm.toPandas()
    spark.stop()

    return df_pandas


def label_segments(df):
    """Assigne un label business à chaque cluster selon ses médianes RFM."""
    stats = df.groupby("cluster").agg(
        recency_med=("recency", "median"),
        frequency_med=("frequency", "median"),
        monetary_med=("monetary", "median"),
    )

    # Score global : on inverse recency (moins = plus récent = mieux)
    stats["score"] = (
        -stats["recency_med"].rank()
        + stats["frequency_med"].rank()
        + stats["monetary_med"].rank()
    )

    rank_to_label = {1: "Champions", 2: "Clients fidèles", 3: "A risque", 4: "Inactifs"}
    ranks = stats["score"].rank(ascending=False, method="first").astype(int)

    return {cluster: rank_to_label[rank] for cluster, rank in ranks.items()}


def run_segmentation():
    engine = get_engine()

    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment("rfm_segmentation")

    with mlflow.start_run():
        # 1. Calcul des features RFM — traitement distribué PySpark → Pandas
        df = compute_rfm_spark()
        print(f"[RFM] {len(df):,} clients analysés")

        # 2. Normalisation
        features = df[["recency", "frequency", "monetary"]].copy()
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # 3. K-Means avec 4 clusters
        n_clusters = 4
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df["cluster"] = kmeans.fit_predict(features_scaled)

        # 4. Métriques
        silhouette = silhouette_score(features_scaled, df["cluster"])
        inertia = kmeans.inertia_
        print(f"[RFM] Silhouette score : {silhouette:.3f} | Inertia : {inertia:.0f}")

        # 5. Labels business
        df["segment"] = df["cluster"].map(label_segments(df))
        print(f"[RFM] Distribution :\n{df['segment'].value_counts().to_string()}")

        # 6. Tracking MLflow
        mlflow.log_param("n_clusters", n_clusters)
        mlflow.log_param("n_customers", len(df))
        mlflow.log_metric("silhouette_score", round(silhouette, 4))
        mlflow.log_metric("inertia", round(inertia, 2))
        for segment, count in df["segment"].value_counts().items():
            mlflow.log_metric(f"n_{segment.replace(' ', '_')}", count)
        mlflow.sklearn.log_model(kmeans, "kmeans_model")

        # 7. Sauvegarde en base
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS analytics.customer_segments"))
            conn.commit()

        df[["customer_unique_id", "recency", "frequency", "monetary", "segment"]].to_sql(
            "customer_segments",
            engine,
            schema="analytics",
            if_exists="replace",
            index=False,
        )
        print("[RFM] Segments sauvegardés dans analytics.customer_segments")

    return silhouette


if __name__ == "__main__":
    run_segmentation()
