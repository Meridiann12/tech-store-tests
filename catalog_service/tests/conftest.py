"""Общая настройка unit-тестов Catalog Service.

Запуск из корня проекта tech-store:
    pytest catalog_service/tests/unit -v
"""
import os
import sys

import pytest

SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from app.repositories import local_product_repo  # noqa: E402


@pytest.fixture(autouse=True)
def clean_storage():
    """Очистка in-memory хранилища товаров перед каждым тестом."""
    local_product_repo._products.clear()
    yield
    local_product_repo._products.clear()
