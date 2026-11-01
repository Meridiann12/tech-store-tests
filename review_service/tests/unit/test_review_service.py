"""Unit-тесты бизнес-логики Review Service.

Ключевое бизнес-правило: оценка товара — целое число от 1 до 5.
"""
import pytest

from app.models.review import ReviewCreate, ReviewStatus
from app.repositories.local_review_repo import ReviewRepo
from app.services.review_service import ReviewService


@pytest.fixture()
def service() -> ReviewService:
    return ReviewService(repo=ReviewRepo())


def _create(service, product_id=501, user_id=42, rating=5):
    return service.create_review(
        ReviewCreate(product_id=product_id, user_id=user_id, rating=rating, text="Отзыв")
    )


def test_create_review(service):
    review = _create(service)
    assert review.review_id > 0
    assert review.status == ReviewStatus.PENDING
    assert review.rating == 5


@pytest.mark.parametrize("rating", [0, 6, -1])
def test_create_review_invalid_rating(service, rating):
    """Оценка вне диапазона 1..5 отклоняется."""
    with pytest.raises(ValueError, match="от 1 до 5"):
        _create(service, rating=rating)


@pytest.mark.parametrize("rating", [1, 5])
def test_create_review_rating_boundaries(service, rating):
    """Границы диапазона (1 и 5) допустимы."""
    assert _create(service, rating=rating).rating == rating


def test_get_product_reviews_filters(service):
    """Возвращаются только отзывы на указанный товар."""
    _create(service, product_id=501)
    _create(service, product_id=501)
    _create(service, product_id=502)
    reviews = service.get_product_reviews(501)
    assert len(reviews) == 2
    assert all(r.product_id == 501 for r in reviews)


def test_moderate_approve(service):
    review = _create(service)
    moderated = service.moderate(review.review_id, approve=True)
    assert moderated.status == ReviewStatus.APPROVED


def test_moderate_reject(service):
    review = _create(service)
    assert service.moderate(review.review_id, approve=False).status == ReviewStatus.REJECTED


def test_moderate_missing_review(service):
    with pytest.raises(KeyError):
        service.moderate(9999, approve=True)


def test_anonymize_user(service):
    """Реакция на user.deleted: отзывы хранятся, но без автора."""
    _create(service, user_id=42)
    _create(service, user_id=42)
    _create(service, user_id=43)
    count = service.anonymize_user(42)
    assert count == 2
    for review in service.repo.get_reviews():
        if review.user_id == 42:
            raise AssertionError("пользователь 42 не анонимизирован")
    assert service.get_product_reviews(501)[0].user_id is None
