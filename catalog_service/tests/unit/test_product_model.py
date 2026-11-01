"""Unit-тесты бизнес-объекта Product (pydantic-модель каталога)."""
import pytest
from pydantic import ValidationError

from app.models.product import Product, ProductCreate, ProductUpdate


def test_product_defaults():
    """Новый товар без отзывов: рейтинг и счётчики нулевые."""
    product = Product(name="Смартфон X", category_id=10, price=59990)
    assert product.rating == 0.0
    assert product.rating_sum == 0.0
    assert product.reviews_count == 0
    assert product.id == 0  # id назначит репозиторий


def test_product_create_required_fields():
    """У ProductCreate обязательны name, category_id и price."""
    data = ProductCreate(name="Смартфон X", category_id=10, price=59990)
    assert data.price == 59990
    with pytest.raises(ValidationError):
        ProductCreate(name="Смартфон X", category_id=10)  # нет price
    with pytest.raises(ValidationError):
        ProductCreate(category_id=10, price=59990)  # нет name


def test_product_update_all_optional():
    """ProductUpdate допускает частичное обновление (оба поля None)."""
    data = ProductUpdate()
    assert data.name is None
    assert data.price is None
    data = ProductUpdate(name="Новое имя", price=1.0)
    assert data.name == "Новое имя"
