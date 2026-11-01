"""Компонентные тесты User Service: http://127.0.0.1:8001/api/users.

Проверяется внешний HTTP-контракт: коды ответов, тела JSON, ошибки 400/404.
"""
import uuid

import pytest
import requests


@pytest.fixture(scope="module")
def created_user(user_svc):
    """Один пользователь на модуль (создаётся в начале, удаляется в конце)."""
    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    resp = requests.post(
        f"{user_svc.base}/users",
        json={"email": email, "full_name": "Иван Иванов"},
    )
    assert resp.status_code == 201, resp.text
    user = resp.json()
    yield user
    requests.delete(f"{user_svc.base}/users/{user['id']}")


def test_get_missing_user_404(user_svc):
    """Пользователя нет -> 404 (хранилище изолированного сервиса пусто)."""
    resp = requests.get(f"{user_svc.base}/users/424242")
    assert resp.status_code == 404


def test_create_user_201(created_user):
    """POST /api/users: 201, id назначен (нумерация с 42), роль USER."""
    assert created_user["id"] >= 42
    assert created_user["role"] == "USER"
    assert "created_at" in created_user


def test_get_user_200(user_svc, created_user):
    resp = requests.get(f"{user_svc.base}/users/{created_user['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == created_user["email"]
    assert body["full_name"] == "Иван Иванов"


def test_create_duplicate_email_400(user_svc, created_user):
    """Повторная регистрация с тем же email -> 400."""
    resp = requests.post(
        f"{user_svc.base}/users",
        json={"email": created_user["email"], "full_name": "Дубль"},
    )
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_get_unknown_user_404(user_svc):
    assert requests.get(f"{user_svc.base}/users/999999").status_code == 404


def test_delete_user(user_svc):
    """DELETE возвращает удалённого пользователя, повторный GET -> 404."""
    email = f"del-{uuid.uuid4().hex[:8]}@example.com"
    user = requests.post(
        f"{user_svc.base}/users",
        json={"email": email, "full_name": "На удаление"},
    ).json()
    resp = requests.delete(f"{user_svc.base}/users/{user['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == user["id"]
    assert requests.get(f"{user_svc.base}/users/{user['id']}").status_code == 404
