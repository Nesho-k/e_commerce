"""
Modèles Pydantic — définissent la structure des données
échangées avec l'API (validation automatique).
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrderItem(BaseModel):
    product_id: str
    seller_id: str
    price: float = Field(..., gt=0)
    freight_value: float = Field(..., ge=0)


class OrderCreate(BaseModel):
    """Schéma d'une commande entrante (POST /orders)."""
    order_id: str
    customer_id: str
    customer_unique_id: str
    customer_city: str
    customer_state: str
    order_status: str = "processing"
    purchased_at: datetime
    estimated_delivery_at: Optional[datetime] = None
    items: list[OrderItem]
    payment_type: str
    payment_value: float = Field(..., gt=0)


class OrderResponse(BaseModel):
    """Schéma de la réponse après insertion."""
    order_id: str
    customer_id: str
    order_status: str
    purchased_at: datetime
    total_items: int
    total_value: float
    message: str
