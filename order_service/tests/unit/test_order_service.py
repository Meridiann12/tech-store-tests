"""Unit-тесты бизнес-логики Order Service.

Здесь особенно важна изоляция от внешних систем. Подменяются обе
внешние зависимости сервиса:
- репозиторий PostgreSQL заменён на FakeOrderRepo (in-memory реализация
  того же интерфейса, что у db_order_repo.OrderRepo) — Dependency Injection;
- синхронный HTTP-вызов Catalog Service заменён моком requests.get.
"""
from unittest.mock import Mock

import pytest
import requests as requests_lib

from app.models.order import OrderCreate, OrderItem, OrderStatus
from app.repositories.db_order_repo import OrderRepo
from app.services.order_service import (
    CatalogUnavailableError,
    OrderService,
    ProductNotFoundError,
)


class FakeOrderRepo(OrderRepo):
    """In-memory репозиторий заказов: тот же интерфейс, что у репозитория
    поверх PostgreSQL, но без обращения к базе (для unit-тестов)."""

    def __init__(self) -> None:
        self._orders = {}
        self._next_id = 1

    def get_orders(self):
        return list(self._orders.values())

    def get_by_id(self, order_id: int):
        if order_id not in self._orders:
            raise KeyError(f"Order {order_id} not found")
        return self._orders[order_id]

    def create_order(self, order):
        order.id = self._next_id
        self._next_id += 1
        self._orders[order.id] = order
        return order

    def change_status(self, order_id: int, status: OrderStatus):
        order = self.get_by_id(order_id)
        order.status = status
        return order

    def anonymize_user(self, user_id: int) -> int:
        count = 0
        for order in self._orders.values():
            if order.user_id == user_id:
                order.user_id = 0
                count += 1
        return count


def _product_response(product: dict) -> Mock:
    """Мок ответа Catalog Service (requests.Response)."""
    resp = Mock()
    resp.status_code = 200
    resp.raise_for_status = Mock()
    resp.json.return_value = {
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
    }
    return resp


@pytest.fixture()
def service(monkeypatch) -> OrderService:
    """Сервис с fake-репозиторием и моком HTTP-вызова каталога."""
    svc = OrderService(repo=FakeOrderRepo())
    monkeypatch.setattr(
        svc,
        "_fetch_product",
        lambda pid: {"id": pid, "name": f"Товар {pid}", "price": 1000.0},
    )
    return svc


def _order_data(*lines) -> OrderCreate:
    return OrderCreate(
        user_id=42,
        items=[OrderItem(product_id=pid, quantity=qty) for pid, qty in lines],
    )


# ---------- оформление заказа ----------

def test_create_order_enriches_items(service):
    """Цены и названия приходят из каталога, сумма считается по позициям."""
    order = service.create_order(_order_data((501, 2), (502, 1)))
    assert order.id > 0
    assert order.status == OrderStatus.CREATED
    assert order.total_price == 3000.0  # 1000 * 2 + 1000 * 1
    assert order.items[0].name == "Товар 501"
    assert order.items[0].price == 1000.0


def test_create_order_persists_via_repo(service):
    """Заказ доступен после создания — сохранён через репозиторий."""
    order = service.create_order(_order_data((501, 1)))
    assert service.get_order(order.id) is order


def test_catalog_unavailable(monkeypatch):
    """Catalog Service недоступен -> CatalogUnavailableError (503 в роутере)."""
    svc = OrderService(repo=FakeOrderRepo())

    def boom(url, timeout=5):
        raise requests_lib.ConnectionError("connection refused")

    monkeypatch.setattr("app.services.order_service.requests.get", boom)
    with pytest.raises(CatalogUnavailableError):
        svc.create_order(_order_data((501, 1)))


def test_product_not_found(monkeypatch):
    """Товара нет в каталоге (404) -> ProductNotFoundError (404 в роутере)."""
    svc = OrderService(repo=FakeOrderRepo())
    resp = Mock()
    resp.status_code = 404
    monkeypatch.setattr("app.services.order_service.requests.get", lambda url, timeout=5: resp)
    with pytest.raises(ProductNotFoundError):
        svc.create_order(_order_data((9999, 1)))


# ---------- смена статусов ----------

def test_change_status(service):
    """Обработка входящих событий inventory.* / payment.*."""
    order = service.create_order(_order_data((501, 1)))
    updated = service.change_status(order.id, OrderStatus.READY_FOR_PAYMENT)
    assert updated.status == OrderStatus.READY_FOR_PAYMENT


def test_cancel_pending_order(service):
    created = service.create_order(_order_data((501, 1)))
    cancelled = service.cancel_order(created.id)
    assert cancelled.status == OrderStatus.CANCELLED


def test_cancel_paid_order_not_changed(service):
    """Оплаченный заказ сразу не отменяется: сначала payment.refunded."""
    order = service.create_order(_order_data((501, 1)))
    service.change_status(order.id, OrderStatus.PAID)
    result = service.cancel_order(order.id)
    assert result.status == OrderStatus.PAID


def test_change_status_missing_order(service):
    with pytest.raises(KeyError):
        service.change_status(9999, OrderStatus.PAID)


# ---------- реакция на user.deleted ----------

def test_anonymize_user(service):
    service.create_order(_order_data((501, 1)))
    service.create_order(_order_data((502, 3)))
    count = service.anonymize_user(42)
    assert count == 2
    for order in service.repo.get_orders():
        assert order.user_id == 0
