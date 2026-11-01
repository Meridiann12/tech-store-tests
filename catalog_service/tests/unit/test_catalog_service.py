"""Unit-тесты бизнес-логики Catalog Service (с локальным репозиторием)."""
import pytest

from app.models.product import ProductCreate, ProductUpdate
from app.repositories.local_product_repo import ProductRepo
from app.services.catalog_service import CatalogService


@pytest.fixture()
def service() -> CatalogService:
    return CatalogService(repo=ProductRepo())


def _create(service, name="Смартфон X", price=59990.0):
    return service.create_product(
        ProductCreate(name=name, category_id=10, price=price)
    )


def test_create_product_assigns_id(service):
    product = _create(service)
    assert product.id > 0
    assert product.price == 59990.0
    assert product.rating == 0.0


def test_get_product(service):
    created = _create(service)
    assert service.get_product(created.id).name == "Смартфон X"


def test_get_missing_product(service):
    with pytest.raises(KeyError):
        service.get_product(9999)


def test_update_price_only(service):
    """Обновление цены не затрагивает название товара."""
    product = _create(service)
    updated = service.update_product(product.id, ProductUpdate(price=54990))
    assert updated.price == 54990
    assert updated.name == "Смартфон X"


def test_update_name_only(service):
    product = _create(service)
    updated = service.update_product(product.id, ProductUpdate(name="Ноутбук"))
    assert updated.name == "Ноутбук"
    assert updated.price == 59990


def test_update_missing_product(service):
    with pytest.raises(KeyError):
        service.update_product(9999, ProductUpdate(price=1))


def test_apply_rating_single_review(service):
    """Первый отзыв: рейтинг равен его оценке."""
    product = _create(service)
    updated = service.apply_review_rating(product.id, 5)
    assert updated.reviews_count == 1
    assert updated.rating_sum == 5
    assert updated.rating == 5.0


def test_apply_rating_average(service):
    """Средний рейтинг пересчитывается по каждому новому отзыву."""
    product = _create(service)
    service.apply_review_rating(product.id, 5)
    updated = service.apply_review_rating(product.id, 4)
    assert updated.reviews_count == 2
    assert updated.rating == 4.5


def test_apply_rating_rounding(service):
    """Средний рейтинг округляется до двух знаков: (5+4+4)/3 = 4.33."""
    product = _create(service)
    for rating in (5, 4, 4):
        updated = service.apply_review_rating(product.id, rating)
    assert updated.rating == 4.33


def test_apply_rating_missing_product(service):
    with pytest.raises(KeyError):
        service.apply_review_rating(9999, 5)
