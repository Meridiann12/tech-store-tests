"""Unit-тесты бизнес-объекта Review (отзыв на товар)."""
import pytest
from pydantic import ValidationError

from app.models.review import Review, ReviewCreate, ReviewStatus


def test_review_default_status():
    """Новый отзыв ожидает модерации (PENDING)."""
    review = Review(
        review_id=9001, product_id=501, user_id=42, rating=5, text="Отличный телефон!"
    )
    assert review.status == ReviewStatus.PENDING


def test_review_user_id_optional():
    """После анонимизации (user.deleted) отзыв хранится без автора."""
    review = Review(
        review_id=9001, product_id=501, user_id=None, rating=5, text="Аноним"
    )
    assert review.user_id is None


def test_review_create_required_fields():
    data = ReviewCreate(product_id=501, user_id=42, rating=5, text="Хорошо")
    assert data.rating == 5
    with pytest.raises(ValidationError):
        ReviewCreate(product_id=501, user_id=42, rating=5)  # нет text
