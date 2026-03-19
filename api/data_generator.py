"""
Générateur de commandes e-commerce réalistes.
Utilise les vraies données Olist (produits, vendeurs, clients)
pour simuler des commandes crédibles.
"""

import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("pt_BR")  # Locale brésilienne pour les noms/villes

# --- Données réalistes tirées du dataset Olist ---

PRODUCT_CATEGORIES = [
    ("bed_bath_table", 89.90),
    ("health_beauty", 59.90),
    ("sports_leisure", 119.90),
    ("furniture_decor", 299.90),
    ("computers_accessories", 189.90),
    ("housewares", 69.90),
    ("watches_gifts", 149.90),
    ("telephony", 249.90),
    ("garden_tools", 79.90),
    ("toys", 49.90),
    ("cool_stuff", 99.90),
    ("electronics", 399.90),
    ("fashion_bags_accessories", 129.90),
    ("office_furniture", 349.90),
    ("stationery", 29.90),
]

PAYMENT_TYPES = [
    ("credit_card", 0.73),   # 73% des paiements (réaliste Olist)
    ("boleto", 0.19),         # 19%
    ("voucher", 0.05),        # 5%
    ("debit_card", 0.03),     # 3%
]

BRAZILIAN_STATES = [
    "SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "ES", "PE"
]

# Délai de livraison moyen réel par état (en jours) — basé sur les stats Olist
# Utilisé pour l'affichage analytique (avg_delivery_days dans Power BI / Streamlit)
DELIVERY_DAYS_BY_STATE = {
    "SP": 8,  "RJ": 11, "MG": 12, "RS": 15, "PR": 11,
    "SC": 13, "BA": 19, "GO": 15, "ES": 14, "PE": 18,
    "CE": 21, "PA": 23, "MA": 21, "MT": 17, "MS": 15,
    "DF": 13, "AL": 24, "AM": 26, "PB": 20, "RN": 19,
    "PI": 19, "SE": 21, "RO": 19, "TO": 17, "AC": 21,
    "AP": 27, "RR": 29,
}

# Saisonnalité : index multiplicateur de volume par mois (1.0 = normal)
SEASONALITY = {
    1: 0.8,   # Janvier : post-fêtes, baisse
    2: 0.9,
    3: 1.0,
    4: 1.0,
    5: 1.1,
    6: 1.0,
    7: 1.1,
    8: 1.0,
    9: 1.0,
    10: 1.1,
    11: 1.5,  # Novembre : Black Friday
    12: 1.4,  # Décembre : fêtes
}


def generate_order_id() -> str:
    """Génère un order_id au format Olist (UUID sans tirets)."""
    return uuid.uuid4().hex


def generate_customer_id() -> str:
    return uuid.uuid4().hex


def pick_payment_type() -> str:
    """Choisit un mode de paiement selon les probabilités réelles Olist."""
    types = [p[0] for p in PAYMENT_TYPES]
    weights = [p[1] for p in PAYMENT_TYPES]
    return random.choices(types, weights=weights, k=1)[0]


def generate_items(
    product_ids: list[str] = None,
    seller_ids: list[str] = None,
    n_items: int = None,
) -> list[dict]:
    """
    Génère entre 1 et 4 articles par commande.
    Utilise les vrais product_id et seller_id si fournis.
    Distribution réaliste : 70% des commandes ont 1 article.
    """
    if n_items is None:
        n_items = random.choices([1, 2, 3, 4], weights=[0.70, 0.20, 0.07, 0.03])[0]

    items = []
    for i in range(n_items):
        category, base_price = random.choice(PRODUCT_CATEGORIES)
        price = round(base_price * random.uniform(0.70, 1.30), 2)
        freight = round(random.uniform(8.0, 45.0), 2)

        items.append({
            "product_id": random.choice(product_ids) if product_ids else uuid.uuid4().hex,
            "seller_id":  random.choice(seller_ids)  if seller_ids  else uuid.uuid4().hex,
            "category": category,
            "price": price,
            "freight_value": freight,
        })
    return items


def generate_order(
    purchased_at: datetime = None,
    product_ids: list[str] = None,
    seller_ids: list[str] = None,
) -> dict:
    """
    Génère une commande complète réaliste.
    Chaque commande crée un nouveau client unique (inséré dans raw_customers).
    Utilise les vrais product_id et seller_id Olist si fournis.
    """
    if purchased_at is None:
        purchased_at = datetime.now()

    state = random.choice(BRAZILIAN_STATES)
    delivery_days = DELIVERY_DAYS_BY_STATE.get(state, 15)
    actual_delivery_days = max(1, delivery_days + random.randint(-3, 3))
    estimated_delivery_at = purchased_at + timedelta(days=actual_delivery_days + 2)

    items = generate_items(product_ids=product_ids, seller_ids=seller_ids)
    total_items_value = sum(i["price"] + i["freight_value"] for i in items)
    payment_type = pick_payment_type()

    return {
        "order_id": generate_order_id(),
        "customer_id": uuid.uuid4().hex,          # ID unique pour cette commande
        "customer_unique_id": uuid.uuid4().hex,    # ID unique du client (fidélité)
        "customer_city": fake.city(),
        "customer_state": state,
        "order_status": "processing",
        "purchased_at": purchased_at.isoformat(),
        "estimated_delivery_at": estimated_delivery_at.isoformat(),
        "delivery_days": actual_delivery_days,
        "items": items,
        "payment_type": payment_type,
        "payment_value": round(total_items_value, 2),
        "total_items": len(items),
    }


def get_seasonality_factor() -> float:
    """Retourne le facteur de saisonnalité du mois courant."""
    return SEASONALITY.get(datetime.now().month, 1.0)


def get_batch_size() -> int:
    """
    Calcule le nombre de commandes à générer par run Airflow (15 min).
    Base : 10 commandes → ~960/jour en période normale.
    Avec saisonnalité : jusqu'à ~1440/jour en novembre (Black Friday).
    """
    base = 10
    factor = SEASONALITY.get(datetime.now().month, 1.0)
    return max(1, int(base * factor * random.uniform(0.7, 1.3)))
