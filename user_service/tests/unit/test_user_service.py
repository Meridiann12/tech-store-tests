"""Unit-тесты бизнес-логики User Service.

Внешние зависимости не используются: в сервис внедряется локальный
(in-memory) репозиторий — паттерн Dependency Injection из методички.
"""
import pytest

from app.models.user import UserCreate, UserRole
from app.repositories.local_user_repo import UserRepo
from app.services.user_service import UserService


@pytest.fixture()
def service() -> UserService:
    # внедряем локальный репозиторий — без обращения к БД и брокеру
    return UserService(repo=UserRepo())


def test_register_user(service):
    """Регистрация: поля заполнены, роль по умолчанию USER, id назначен."""
    user = service.register_user(
        UserCreate(email="client@example.com", full_name="Иван Иванов")
    )
    assert user.id > 0
    assert user.email == "client@example.com"
    assert user.full_name == "Иван Иванов"
    assert user.role == UserRole.USER
    # пользователь действительно сохранён в репозитории
    assert service.get_user(user.id) is user


def test_register_duplicate_email(service):
    """Повторная регистрация с тем же email запрещена."""
    service.register_user(UserCreate(email="dup@example.com", full_name="Первый"))
    with pytest.raises(ValueError, match="already exists"):
        service.register_user(UserCreate(email="dup@example.com", full_name="Второй"))


def test_get_missing_user(service):
    """Несуществующий пользователь -> KeyError (превратится в 404 в роутере)."""
    with pytest.raises(KeyError):
        service.get_user(9999)


def test_delete_user(service):
    """Удаление возвращает удалённого пользователя и убирает его из хранилища."""
    user = service.register_user(
        UserCreate(email="gone@example.com", full_name="На удаление")
    )
    deleted = service.delete_user(user.id)
    assert deleted.id == user.id
    with pytest.raises(KeyError):
        service.get_user(user.id)


def test_delete_missing_user(service):
    """Удаление несуществующего пользователя -> KeyError."""
    with pytest.raises(KeyError):
        service.delete_user(9999)


def test_ids_are_incremented(service):
    """Репозиторий назначает уникальные возрастающие идентификаторы."""
    u1 = service.register_user(UserCreate(email="a@example.com", full_name="A"))
    u2 = service.register_user(UserCreate(email="b@example.com", full_name="B"))
    assert u2.id == u1.id + 1
