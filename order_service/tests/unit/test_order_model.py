"""Unit-тесты бизнес-объекта Order (заказ)."""
import pytest
from pydantic import ValidationError

from app.models.order import OrderCreate, OrderItem, OrderStatus


def test_order_item_optional_fields():
    """Цену и название сервис получает из Catalog Service при оформлении."""
    item = OrderItem(product_id=501, quantity=2)
    assert item.price is None
    assert item.name is None


def test_order_statuses_enum():
    assert {s.value for s in OrderStatus} == {
        "CREATED",
        "READY_FOR_PAYMENT",
        "PAID",
        "CANCELLED",
        "RETURNED",
    }


def test_order_create_requires_items():
    """Заказ без позиций не проходит валидацию."""
    with pytest.raises(ValidationError):
        OrderCreate(user_id=42)
