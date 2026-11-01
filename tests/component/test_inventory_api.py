"""Компонентные тесты Inventory Service: http://127.0.0.1:8003/api/inventory."""
import requests


def test_get_unknown_stock_404(inventory_svc):
    """Остатка нет -> 404 (в docker compose он создаётся по product.created)."""
    assert requests.get(f"{inventory_svc.base}/inventory/999999").status_code == 404


def test_supply_creates_stock(inventory_svc):
    """Первая приёмка создаёт запись остатка с полученным количеством."""
    resp = requests.post(
        f"{inventory_svc.base}/inventory/501/supply", json={"amount": 10}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["product_id"] == 501
    assert body["quantity"] == 10
    assert body["reserved"] == 0


def test_supply_accumulates(inventory_svc):
    """Повторная приёмка суммируется с текущим остатком."""
    resp = requests.post(
        f"{inventory_svc.base}/inventory/501/supply", json={"amount": 5}
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 15


def test_get_stock_200(inventory_svc):
    resp = requests.get(f"{inventory_svc.base}/inventory/501")
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 15


def test_supply_non_positive_400(inventory_svc):
    """Приёмка с amount = 0 -> 400 (бизнес-правило сервиса)."""
    resp = requests.post(
        f"{inventory_svc.base}/inventory/502/supply", json={"amount": 0}
    )
    assert resp.status_code == 400
