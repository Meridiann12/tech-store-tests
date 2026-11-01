"""Unit-тесты бизнес-объекта User (pydantic-модель).

По методичке на этапе unit-тестирования сначала тестируются
бизнес-объекты: обязательные и необязательные поля, значения по умолчанию.
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.user import User, UserCreate, UserRole


def test_user_defaults():
    """Роль по умолчанию — USER, created_at заполняется автоматически."""
    user = User(email="client@example.com", full_name="Иван Иванов")
    assert user.role == UserRole.USER
    assert user.id == 0  # id назначит репозиторий при создании
    assert isinstance(user.created_at, datetime)


def test_user_full_construction():
    """Все поля можно задать явно, включая роль."""
    user = User(
        id=42,
        email="admin@example.com",
        full_name="Анна Петрова",
        role=UserRole.ADMIN,
    )
    assert user.id == 42
    assert user.role == UserRole.ADMIN
    assert user.email == "admin@example.com"


def test_user_email_required():
    """email — обязательное поле: pydantic выбрасывает ValidationError."""
    with pytest.raises(ValidationError):
        User(full_name="Иван Иванов")


def test_user_create_requires_full_name():
    """У UserCreate обязательны и email, и full_name."""
    data = UserCreate(email="client@example.com", full_name="Иван Иванов")
    assert data.email == "client@example.com"
    with pytest.raises(ValidationError):
        UserCreate(email="client@example.com")  # full_name не передан


def test_user_roles_enum():
    """Роль — перечисление из трёх значений."""
    assert {r.value for r in UserRole} == {"USER", "MANAGER", "ADMIN"}
