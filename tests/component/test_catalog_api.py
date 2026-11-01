"""Компонентные тесты Catalog Service: http://127.0.0.1:8002/api/products."""
import pytest
import requests


@pytest.fixture(scope="module")
def product(catalog):
    resp = requests.post(
        f"{catalog.base}/products",
        json={"name": "Смартфон X", "category_id": 10, "price": 59990},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_product_201(product):
    """POST /api/products: 201, товар без рейтинга (отзывов ещё нет)."""
    assert product["id"] >= 501  # нумерация товаров с 501
    assert product["name"] == "Смартфон X"
    assert product["price"] == 59990
    assert product["rating"] == 0.0


def test_get_product_200(catalog, product):
    resp = requests.get(f"{catalog.base}/products/{product['id']}")
    assert resp.status_code == 200
    assert resp.json()["price"] == 59990


def test_get_unknown_product_404(catalog):
    assert requests.get(f"{catalog.base}/products/999999").status_code == 404


def test_update_price_partial(catalog, product):
    """PUT обновляет только переданные поля (частичное обновление)."""
    resp = requests.put(
        f"{catalog.base}/products/{product['id']}", json={"price": 54990}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["price"] == 54990
    assert body["name"] == "Смартфон X"  # название не изменилось
