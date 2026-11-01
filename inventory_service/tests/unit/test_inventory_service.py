"""Unit-тесты бизнес-логики Inventory Service (склад: приёмка, резервы)."""
import pytest

from app.models.stock import StockItem
from app.repositories.local_stock_repo import StockRepo
from app.services.inventory_service import InventoryService


@pytest.fixture()
def service() -> InventoryService:
    return InventoryService(repo=StockRepo())


# ---------- приёмка товара ----------

def test_supply_creates_stock(service):
    """Первая приёмка создаёт запись остатка."""
    item = service.supply(501, 10)
    assert item.product_id == 501
    assert item.quantity == 10
    assert item.reserved == 0


def test_supply_accumulates(service):
    """Повторные приёмки суммируются."""
    service.supply(501, 10)
    item = service.supply(501, 5)
    assert item.quantity == 15


@pytest.mark.parametrize("amount", [0, -3])
def test_supply_non_positive_raises(service, amount):
    """Приёмка нуля или отрицательного количества запрещена."""
    with pytest.raises(ValueError):
        service.supply(501, amount)


def test_create_initial_stock_idempotent(service):
    """Реакция на product.created: повторное событие не плодит записи."""
    first = service.create_initial_stock(501)
    second = service.create_initial_stock(501)
    assert first is second
    assert len(service.get_all()) == 1


# ---------- резерв под заказ ----------

def test_reserve_success(service):
    """Достаточно товара на всех позициях — резерв оформлен."""
    service.supply(501, 10)
    service.supply(502, 3)
    result = service.reserve_for_order(
        1,
        [{"product_id": 501, "quantity": 4}, {"product_id": 502, "quantity": 3}],
    )
    assert result["status"] == "reserved"
    assert service.get_stock(501).reserved == 4
    assert service.get_stock(502).reserved == 3


def test_reserve_insufficient(service):
    """Нехватка товара: статус failed, перечень missing_products, без резерва."""
    service.supply(501, 2)
    result = service.reserve_for_order(1, [{"product_id": 501, "quantity": 5}])
    assert result["status"] == "failed"
    assert result["missing_products"][0]["available"] == 2
    assert result["missing_products"][0]["requested"] == 5
    assert service.get_stock(501).reserved == 0


def test_reserve_unknown_product(service):
    """Товар без записи остатка попадает в missing_products."""
    result = service.reserve_for_order(1, [{"product_id": 777, "quantity": 1}])
    assert result["status"] == "failed"
    assert result["missing_products"][0]["available"] == 0


def test_reserve_counts_available_minus_reserved(service):
    """Доступно = quantity - reserved: повторный заказ учитывает резерв."""
    service.supply(501, 10)
    service.reserve_for_order(1, [{"product_id": 501, "quantity": 8}])
    result = service.reserve_for_order(2, [{"product_id": 501, "quantity": 3}])
    assert result["status"] == "failed"  # доступно только 2 из 3


def test_release_reserve(service):
    """Реакция на order.cancelled: резерв возвращается на склад."""
    service.supply(501, 10)
    service.reserve_for_order(1, [{"product_id": 501, "quantity": 4}])
    service.release_reserve(1, [{"product_id": 501, "quantity": 4}])
    assert service.get_stock(501).reserved == 0


def test_release_reserve_floor_zero(service):
    """Резерв не уходит в минус при лишнем снятии."""
    service.supply(501, 10)
    service.release_reserve(1, [{"product_id": 501, "quantity": 3}])
    assert service.get_stock(501).reserved == 0


# ---------- бизнес-правило низкого остатка ----------

def test_is_low_stock(service):
    """Остаток ниже порога 5 -> уведомление inventory.low_stock."""
    item = service.supply(501, 3)
    assert service.is_low_stock(item) is True
    item2 = service.supply(502, 10)
    assert service.is_low_stock(item2) is False
