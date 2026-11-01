"""Unit-тесты бизнес-логики Payment Service.

Проверяются ключевые бизнес-правила: лимит платежа 200 000 руб.,
одна транзакция на заказ, возврат средств по оплаченным заказам.
"""
import pytest

from app.models.payment import PaymentStatus
from app.repositories.local_payment_repo import PaymentRepo
from app.services.payment_service import PAYMENT_LIMIT, PaymentService


@pytest.fixture()
def service() -> PaymentService:
    return PaymentService(repo=PaymentRepo())


# ---------- создание транзакции по событию order.created ----------

def test_create_transaction_pending(service):
    payment = service.create_transaction(order_id=1, amount=119980)
    assert payment.status == PaymentStatus.PENDING
    assert payment.order_id == 1
    assert payment.payment_id > 0


def test_create_transaction_idempotent(service):
    """Повторное событие order.created не создаёт вторую транзакцию."""
    first = service.create_transaction(order_id=1, amount=119980)
    second = service.create_transaction(order_id=1, amount=119980)
    assert first is second
    assert len(service.get_payments()) == 1


# ---------- проведение платежа ----------

def test_pay_under_limit(service):
    """Сумма в пределах лимита: платёж проведён (PAID)."""
    service.create_transaction(order_id=1, amount=119980)
    payment = service.pay(1)
    assert payment.status == PaymentStatus.PAID


def test_pay_exact_limit(service):
    """Граница правила: ровно 200 000 руб. — лимит не превышен."""
    service.create_transaction(order_id=2, amount=PAYMENT_LIMIT)
    assert service.pay(2).status == PaymentStatus.PAID


def test_pay_over_limit_fails(service):
    """Платёж свыше 200 000 руб. отклоняется (payment.failed)."""
    service.create_transaction(order_id=3, amount=250000)
    payment = service.pay(3)
    assert payment.status == PaymentStatus.FAILED


def test_pay_twice_raises(service):
    """Повторная оплата той же транзакции невозможна."""
    service.create_transaction(order_id=1, amount=1000)
    service.pay(1)
    with pytest.raises(ValueError, match="оплата невозможна"):
        service.pay(1)


def test_pay_missing_transaction(service):
    with pytest.raises(KeyError):
        service.pay(9999)


# ---------- возврат средств по событию order.cancelled ----------

def test_refund_paid_order(service):
    """Оплаченный заказ: возврат средств -> REFUNDED."""
    service.create_transaction(order_id=1, amount=119980)
    service.pay(1)
    refunded = service.refund_if_paid(1)
    assert refunded.status == PaymentStatus.REFUNDED


def test_refund_skips_pending(service):
    """Неоплаченный заказ возврата не требует: ничего не меняем."""
    service.create_transaction(order_id=1, amount=119980)
    assert service.refund_if_paid(1) is None
    assert service.get_payment(1).status == PaymentStatus.PENDING


def test_refund_unknown_order(service):
    assert service.refund_if_paid(9999) is None
