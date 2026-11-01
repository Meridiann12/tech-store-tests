"""Общая настройка unit-тестов Review Service.

Запуск из корня проекта tech-store:
    pytest review_service/tests/unit -v
"""
import os
import sys

import pytest

SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from app.repositories import local_review_repo  # noqa: E402


@pytest.fixture(autouse=True)
def clean_storage():
    """Очистка in-memory хранилища отзывов перед каждым тестом."""
    local_review_repo._reviews.clear()
    yield
    local_review_repo._reviews.clear()
