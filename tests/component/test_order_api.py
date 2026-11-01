"""Компонентные тесты Order Service в связке с Catalog Service.

Ключевой сценарий межсервисного взаимодействия: POST /api/orders получает
цены и названия товаров синхронным HTTP-вызовом реального Catalog Service
(CATALOG_URL -> процесс на порту 8002), заказ сохраняется через
SQLAlchemy-репозиторий (SQLite для изолированного прогона).
"""
import pytest
import requests


@pytest.fixture(scope="module")
def order_ctx(order_svc, catalog):
    """Товар в каталоге + заказ на него (создаются один раз на модуль)."""
    product = requests.post(
        f"{catalog.base}/products",
        json={"name": "Ноутбук Pro", "category_id": 20, "price": 99990},
    ).json()
    resp = requests.post(
        f"{order_svc.base}/orders",
        json={"user_id": 42, "items": [{"product_id": product["id"], "quantity": 2}]},
    )
    assert resp.status_code == 201, resp.text
    return {"product": product, "order": resp.json()}


def test_create_order_enriched_by_catalog(order_ctx):
    """В ответе есть price и name, отсутствовавшие в запросе, — они
    получены у Catalog Service; сумма посчитана по цене каталога."""
    order = order_ctx["order"]
    assert order["status"] == "CREATED"
    assert order["items"][0]["name"] == "Ноутбук Pro"
    assert order["items"][0]["price"] == 99990
    assert order["total_price"] == 199980.0
    assert order["user_id"] == 42


def test_get_order_200(order_svc, order_ctx):
    """Заказ читается обратно из СУБД через GET /api/orders/{id}."""
    order_id = order_ctx["order"]["id"]
    resp = requests.get(f"{order_svc.base}/orders/{order_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "CREATED"
    assert body["total_price"] == 199980.0


def test_get_unknown_order_404(order_svc):
    assert requests.get(f"{order_svc.base}/orders/999999").status_code == 404


def test_create_order_unknown_product_404(order_svc):
    """Товара нет в каталоге -> Catalog вернул 404 -> клиент получает 404."""
    resp = requests.post(
        f"{order_svc.base}/orders",
        json={"user_id": 42, "items": [{"product_id": 999999, "quantity": 1}]},
    )
    assert resp.status_code == 404


def test_cancel_order(order_svc, order_ctx):
    """POST /api/orders/{id}/cancel: заказ уходит в CANCELLED."""
    order_id = order_ctx["order"]["id"]
    resp = requests.post(f"{order_svc.base}/orders/{order_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"
    # статус сохранился в базе
    assert requests.get(f"{order_svc.base}/orders/{order_id}").json()["status"] == "CANCELLED"
