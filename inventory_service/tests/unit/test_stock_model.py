"""Unit-тесты бизнес-объекта StockItem (остаток склада)."""
import pytest
from pydantic import ValidationError

from app.models.stock import StockItem, SupplyRequest


def test_stock_defaults():
    """Новая запись остатка: нулевые количество и резерв, порог 5."""
    item = StockItem(product_id=501)
    assert item.quantity == 0
    assert item.reserved == 0
    assert item.threshold == 5  # бизнес-правило по умолчанию


def test_supply_request_requires_amount():
    """SupplyRequest хранит только объём приёмки."""
    assert SupplyRequest(amount=10).amount == 10
    with pytest.raises(ValidationError):
        SupplyRequest()  # amount обязателен
