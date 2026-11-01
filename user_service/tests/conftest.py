"""Общая настройка unit-тестов User Service.

Запуск из корня проекта tech-store:
    pytest user_service/tests/unit -v
"""
import os
import sys

import pytest

# чтобы импорты app.* указывали на пакеты ИМЕННО этого сервиса
SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from app.repositories import local_user_repo  # noqa: E402


@pytest.fixture(autouse=True)
def clean_storage():
    """Репозиторий хранит пользователей в списке на уровне модуля.

    Перед каждым тестом очищаем хранилище, чтобы тесты были
    независимы друг от друга и от порядка запуска.
    """
    local_user_repo._users.clear()
    yield
    local_user_repo._users.clear()
