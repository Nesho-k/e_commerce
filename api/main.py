"""
API FastAPI — génération et ingestion de commandes e-commerce.
"""

import os
import uuid
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from api.models import OrderCreate, OrderResponse
from api.data_generator import generate_order, get_seasonality_factor, get_batch_size

load_dotenv()

# --- Connexion PostgreSQL ---
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
engine = create_engine(DATABASE_URL)

# --- Cache des vrais IDs Olist (chargés au démarrage) ---
REAL_IDS = {"product_ids": [], "seller_ids": []}

# --- App FastAPI ---
app = FastAPI(
    title="E-commerce Analytics API",
    description="API de simulation et ingestion de commandes e-commerce en temps réel.",
    version="1.0.0",
)


@app.on_event("startup")
def load_real_ids():
    """Charge les vrais product_ids et seller_ids Olist au démarrage de l'API."""
    with engine.connect() as conn:
        REAL_IDS["product_ids"] = [
            r[0] for r in conn.execute(text("SELECT product_id FROM raw.raw_products LIMIT 5000"))
        ]
        REAL_IDS["seller_ids"] = [
            r[0] for r in conn.execute(text("SELECT seller_id FROM raw.raw_sellers"))
        ]
    print(f"[STARTUP] IDs chargés : "
          f"{len(REAL_IDS['product_ids'])} produits, "
          f"{len(REAL_IDS['seller_ids'])} vendeurs")


# ---------------------------------------------------------------
# ENDPOINT 1 : Health check
# ---------------------------------------------------------------
@app.get("/", tags=["Monitoring"])
def health_check():
    """Vérifie que l'API et la base de données sont opérationnelles."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


# ---------------------------------------------------------------
# ENDPOINT 2 : Générer une commande aléatoire
# ---------------------------------------------------------------
@app.get("/orders/generate", tags=["Orders"])
def generate_random_order():
    """
    Génère une commande aléatoire réaliste sans l'insérer en base.
    Utile pour tester le pipeline ou prévisualiser les données.
    """
    order = generate_order(**REAL_IDS)
    order["seasonality_factor"] = get_seasonality_factor()
    return order


# ---------------------------------------------------------------
# ENDPOINT 3 : Insérer une commande en base
# ---------------------------------------------------------------
@app.post("/orders", response_model=OrderResponse, tags=["Orders"])
def create_order(order: OrderCreate):
    """
    Insère une nouvelle commande dans la table raw.raw_orders
    et ses articles dans raw.raw_order_items.
    """
    try:
        with engine.connect() as conn:

            # Insertion du nouveau client dans raw_customers
            conn.execute(text("""
                INSERT INTO raw.raw_customers (
                    customer_id, customer_unique_id,
                    customer_city, customer_state
                ) VALUES (
                    :customer_id, :customer_unique_id,
                    :customer_city, :customer_state
                )
            """), {
                "customer_id":        order.customer_id,
                "customer_unique_id": order.customer_unique_id,
                "customer_city":      order.customer_city,
                "customer_state":     order.customer_state,
            })

            # Insertion dans raw_orders
            conn.execute(text("""
                INSERT INTO raw.raw_orders (
                    order_id, customer_id, order_status,
                    order_purchase_timestamp,
                    order_estimated_delivery_date
                ) VALUES (
                    :order_id, :customer_id, :order_status,
                    :purchased_at, :estimated_delivery_at
                )
            """), {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "order_status": order.order_status,
                "purchased_at": order.purchased_at,
                "estimated_delivery_at": order.estimated_delivery_at,
            })

            # Insertion des articles dans raw_order_items
            for idx, item in enumerate(order.items, start=1):
                conn.execute(text("""
                    INSERT INTO raw.raw_order_items (
                        order_id, order_item_id, product_id,
                        seller_id, price, freight_value
                    ) VALUES (
                        :order_id, :item_id, :product_id,
                        :seller_id, :price, :freight_value
                    )
                """), {
                    "order_id": order.order_id,
                    "item_id": idx,
                    "product_id": item.product_id,
                    "seller_id": item.seller_id,
                    "price": item.price,
                    "freight_value": item.freight_value,
                })

            # Insertion du paiement dans raw_order_payments
            conn.execute(text("""
                INSERT INTO raw.raw_order_payments (
                    order_id, payment_sequential, payment_type, payment_value
                ) VALUES (
                    :order_id, 1, :payment_type, :payment_value
                )
            """), {
                "order_id": order.order_id,
                "payment_type": order.payment_type,
                "payment_value": order.payment_value,
            })

            conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur insertion : {str(e)}")

    return OrderResponse(
        order_id=order.order_id,
        customer_id=order.customer_id,
        order_status=order.order_status,
        purchased_at=order.purchased_at,
        total_items=len(order.items),
        total_value=order.payment_value,
        message="Commande insérée avec succès.",
    )


# ---------------------------------------------------------------
# ENDPOINT 4 : Générer ET insérer une commande d'un coup
# ---------------------------------------------------------------
@app.post("/orders/generate-and-insert", tags=["Orders"])
def generate_and_insert():
    """
    Génère une commande aléatoire et l'insère directement en base.
    Simule l'arrivée d'une vraie commande en temps réel.
    """
    raw = generate_order(**REAL_IDS)

    order = OrderCreate(
        order_id=raw["order_id"],
        customer_id=raw["customer_id"],
        customer_unique_id=raw["customer_unique_id"],
        customer_city=raw["customer_city"],
        customer_state=raw["customer_state"],
        order_status=raw["order_status"],
        purchased_at=datetime.fromisoformat(raw["purchased_at"]),
        estimated_delivery_at=datetime.fromisoformat(raw["estimated_delivery_at"]),
        items=raw["items"],
        payment_type=raw["payment_type"],
        payment_value=raw["payment_value"],
    )

    return create_order(order)


# ---------------------------------------------------------------
# ENDPOINT 5 : Générer un batch de commandes (saisonnalité)
# ---------------------------------------------------------------
@app.post("/orders/batch", tags=["Orders"])
def generate_batch():
    """
    Génère plusieurs commandes en une fois selon la saisonnalité.
    Appelé par Airflow toutes les 15 minutes.
    Novembre (Black Friday) → plus de commandes qu'en janvier.
    """
    n = get_batch_size()
    results = []
    for _ in range(n):
        raw = generate_order(**REAL_IDS)
        order = OrderCreate(
            order_id=raw["order_id"],
            customer_id=raw["customer_id"],
            customer_unique_id=raw["customer_unique_id"],
            customer_city=raw["customer_city"],
            customer_state=raw["customer_state"],
            order_status=raw["order_status"],
            purchased_at=datetime.fromisoformat(raw["purchased_at"]),
            estimated_delivery_at=datetime.fromisoformat(raw["estimated_delivery_at"]),
            items=raw["items"],
            payment_type=raw["payment_type"],
            payment_value=raw["payment_value"],
        )
        result = create_order(order)
        results.append(result)

    return {
        "orders_generated": n,
        "seasonality_factor": get_seasonality_factor(),
        "orders": results,
    }


# ---------------------------------------------------------------
# ENDPOINT 6 : Mettre à jour les statuts des commandes
# ---------------------------------------------------------------
@app.post("/orders/update-statuses", tags=["Orders"])
def update_order_statuses():
    """
    Fait évoluer les statuts des commandes en attente.
    - processing  → shipped   après 15 minutes réelles
    - shipped     → delivered après 45 minutes réelles

    Cycle complet ~45 min → les commandes apparaissent dans les KPIs.
    """
    try:
        with engine.connect() as conn:
            # processing → shipped (après 15 min)
            result_shipped = conn.execute(text("""
                UPDATE raw.raw_orders
                SET order_status = 'shipped',
                    order_delivered_carrier_date = NOW()
                WHERE order_status = 'processing'
                  AND order_purchase_timestamp::timestamp <= NOW() - INTERVAL '15 minutes'
                  AND order_purchase_timestamp::timestamp >= '2026-01-01'
                RETURNING order_id
            """))
            shipped_ids = [row[0] for row in result_shipped]

            # shipped → delivered (après 45 min depuis achat)
            # delivered_at = purchased_at + (estimated - purchased_at) * facteur réaliste
            # 90% livré avant la date estimée, 10% en retard
            result_delivered = conn.execute(text("""
                UPDATE raw.raw_orders
                SET order_status = 'delivered',
                    order_delivered_customer_date = (
                        order_purchase_timestamp::timestamp +
                        (order_estimated_delivery_date::timestamp - order_purchase_timestamp::timestamp)
                        * (CASE WHEN RANDOM() < 0.90
                                THEN (0.65 + RANDOM() * 0.30)
                                ELSE (1.01 + RANDOM() * 0.15)
                           END)
                    )
                WHERE order_status = 'shipped'
                  AND order_purchase_timestamp::timestamp <= NOW() - INTERVAL '45 minutes'
                  AND order_purchase_timestamp::timestamp >= '2026-01-01'
                RETURNING order_id, order_delivered_customer_date
            """))
            delivered_rows = [(row[0], row[1]) for row in result_delivered]
            delivered_ids = [r[0] for r in delivered_rows]

            # Génération des reviews pour les commandes livrées
            for order_id, delivered_at in delivered_rows:
                score = random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.06, 0.04, 0.08, 0.19, 0.63]
                )[0]
                conn.execute(text("""
                    INSERT INTO raw.raw_order_reviews
                        (review_id, order_id, review_score, review_creation_date)
                    VALUES (:review_id, :order_id, :score, :created_at)
                """), {
                    "review_id": uuid.uuid4().hex,
                    "order_id": order_id,
                    "score": score,
                    "created_at": delivered_at,
                })

            conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur update statuts : {str(e)}")

    return {
        "shipped": len(shipped_ids),
        "delivered": len(delivered_ids),
        "message": f"{len(shipped_ids)} expédiées, {len(delivered_ids)} livrées.",
    }
