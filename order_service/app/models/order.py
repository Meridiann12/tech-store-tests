import enum
from datetime import datetime

from pydantic import BaseModel


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    READY_FOR_PAYMENT = "READY_FOR_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float | None = None
    name: str | None = None


class Order(BaseModel):
    """Анемичная модель заказа: только данные, без поведения."""

    id: int
    user_id: int
    status: OrderStatus
    items: list[OrderItem]
    total_price: float
    created_at: datetime


class OrderCreate(BaseModel):
    user_id: int
    items: list[OrderItem]
