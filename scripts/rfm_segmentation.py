"""
RFM Segmentation avec K-Means
Calcule les scores Recency, Frequency, Monetary par client
et applique un clustering K-Means pour segmenter les clients.
Les résultats sont trackés avec MLflow et sauvegardés dans analytics.customer_segments.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import mlflow
import mlflow.sklearn
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)


def compute_rfm(engine):
    """Calcule les features RFM par client unique."""
    query = """
    SELECT
        c.customer_unique_id,
        MAX(o.purchased_at)          AS last_order_date,
        COUNT(DISTINCT o.order_id)   AS frequency,
        SUM(p.total_payment)         AS monetary
    FROM clean.customers c
    JOIN clean.orders o  ON c.customer_id = o.customer_id
    JOIN clean.payments p ON o.order_id   = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    reference_date = df["last_order_date"].max()
    df["recency"] = (reference_date - df["last_order_date"]).dt.days

    return df[["customer_unique_id", "recency", "frequency", "monetary"]]


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
        # 1. Calcul des features RFM
        df = compute_rfm(engine)
        print(f"[RFM] {len(df)} clients analysés")

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
