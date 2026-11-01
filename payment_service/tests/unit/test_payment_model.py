"""Unit-тесты бизнес-объекта Payment (транзакция платежа)."""
import pytest
from pydantic import ValidationError

from app.models.payment import Payment, PaymentStatus


def test_payment_default_status():
    """Транзакция создаётся в статусе PENDING и ждёт оплату."""
    payment = Payment(payment_id=555, order_id=1, amount=119980)
    assert payment.status == PaymentStatus.PENDING


def test_payment_statuses_enum():
    assert {s.value for s in PaymentStatus} == {"PENDING", "PAID", "FAILED", "REFUNDED"}


def test_payment_required_fields():
    with pytest.raises(ValidationError):
        Payment(payment_id=555)  # нет order_id и amount
