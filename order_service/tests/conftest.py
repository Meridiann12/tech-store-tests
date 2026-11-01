"""Общая настройка unit-тестов Order Service.

Запуск из корня проекта tech-store:
    pytest order_service/tests/unit -v
"""
import os
import sys

# Модуль app.database создаёт SQLAlchemy-engine при импорте. Unit-тесты
# не работают с базой (репозиторий подменяется FakeOrderRepo), поэтому
# движку указывается встроенная SQLite-заглушка ещё до импортов app.*.
os.environ.setdefault("POSTGRES_URL", "sqlite://")

# чтобы импорты app.* указывали на пакеты ИМЕННО этого сервиса
SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)
