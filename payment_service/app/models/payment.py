import enum
from datetime import datetime

from pydantic import BaseModel, Field


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(BaseModel):
    """Анемичная модель платежа: статус платежа независим от статуса заказа."""

    payment_id: int
    order_id: int
    amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
