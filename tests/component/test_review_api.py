"""Компонентные тесты Review Service: http://127.0.0.1:8006/api/reviews."""
import pytest
import requests


@pytest.fixture(scope="module")
def review(review_svc):
    resp = requests.post(
        f"{review_svc.base}/reviews",
        json={
            "product_id": 501,
            "user_id": 42,
            "rating": 5,
            "text": "Отличный телефон!",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_review_201(review):
    """POST /api/reviews: 201, отзыв в статусе PENDING, нумерация с 9001."""
    assert review["review_id"] >= 9001
    assert review["status"] == "PENDING"
    assert review["rating"] == 5


def test_create_review_invalid_rating_400(review_svc):
    """Оценка 6 вне диапазона 1..5 -> 400."""
    resp = requests.post(
        f"{review_svc.base}/reviews",
        json={"product_id": 501, "user_id": 42, "rating": 6, "text": "Плохо"},
    )
    assert resp.status_code == 400
    assert "от 1 до 5" in resp.json()["detail"]


def test_get_product_reviews(review_svc, review):
    """GET /api/reviews/product/{id}: отзыв на месте."""
    resp = requests.get(f"{review_svc.base}/reviews/product/501")
    assert resp.status_code == 200
    ids = [r["review_id"] for r in resp.json()]
    assert review["review_id"] in ids


def test_moderate_approve(review_svc, review):
    """POST /api/reviews/{id}/moderate: статус меняется на APPROVED."""
    resp = requests.post(
        f"{review_svc.base}/reviews/{review['review_id']}/moderate",
        json={"approve": True},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"


def test_moderate_unknown_404(review_svc):
    resp = requests.post(
        f"{review_svc.base}/reviews/999999/moderate", json={"approve": True}
    )
    assert resp.status_code == 404
