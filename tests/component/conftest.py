"""Компонентные (e2e) тесты системы Tech Store.

Сервисы тестируются «снаружи», как в методичке: каждый поднимается
реальным процессом uvicorn, тесты обращаются к нему по HTTP через
внешний контракт (роутер /api/*) библиотекой requests.

Внутренние функции сервисов не вызываются — проверяется только то,
что доступно внешнему клиенту.

Запуск из корня проекта tech-store:
    pytest tests/component -v

Особенности окружения тестов:
- RabbitMQ в прогоне не участвует: асинхронные события не доставляются
  (publish_event печатает [WARN] и продолжает работу);
- PostgreSQL заменён на SQLite-файл (POSTGRES_URL): репозиторий Order
  Service реализован поверх SQLAlchemy и не привязан к диалекту СУБД;
- синхронный вызов Catalog Service из Order Service работает по-настоящему:
  оба сервиса запущены, CATALOG_URL указывает на реальный процесс.
"""
import os
import subprocess
import sys
import tempfile
import time

import pytest
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = sys.executable
READY_TIMEOUT = 60.0


def _wait_ready(url: str, timeout: float = READY_TIMEOUT) -> None:
    """Ждём, пока сервис начнёт отвечать по HTTP."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(url, timeout=2).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.25)
    raise RuntimeError(f"Сервис не ответил за {timeout:.0f} с: {url}")


class ServiceProcess:
    """Запущенный экземпляр микросервиса (процесс uvicorn)."""

    def __init__(self, service_dir: str, port: int, env: dict | None = None):
        self.port = port
        log = tempfile.NamedTemporaryFile(
            prefix=f"uvicorn_{port}_", suffix=".log", delete=False
        )
        self.log_path = log.name
        self.proc = subprocess.Popen(
            [
                PYTHON, "-m", "uvicorn", "app.main:app",
                "--host", "127.0.0.1", "--port", str(port),
                "--log-level", "warning",
            ],
            cwd=service_dir,
            env={**os.environ, **(env or {})},
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}/api"

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


def _start(name: str, port: int, env: dict | None = None) -> ServiceProcess:
    svc = ServiceProcess(os.path.join(ROOT, name), port, env)
    try:
        _wait_ready(f"http://127.0.0.1:{port}/docs")
    except Exception:
        svc.stop()
        with open(svc.log_path, encoding="utf-8") as f:
            print(f"[{name}] лог запуска:\n{f.read()}")
        raise
    return svc


# ---------- фикстуры: по одному экземпляру каждого сервиса на сессию ----------

@pytest.fixture(scope="session")
def user_svc() -> ServiceProcess:
    svc = _start("user_service", 8001)
    yield svc
    svc.stop()


@pytest.fixture(scope="session")
def catalog() -> ServiceProcess:
    svc = _start("catalog_service", 8002)
    yield svc
    svc.stop()


@pytest.fixture(scope="session")
def inventory_svc() -> ServiceProcess:
    svc = _start("inventory_service", 8003)
    yield svc
    svc.stop()


@pytest.fixture(scope="session")
def payment_svc() -> ServiceProcess:
    svc = _start("payment_service", 8005)
    yield svc
    svc.stop()


@pytest.fixture(scope="session")
def review_svc() -> ServiceProcess:
    svc = _start("review_service", 8006)
    yield svc
    svc.stop()


@pytest.fixture(scope="session")
def order_svc(catalog) -> ServiceProcess:
    """Order Service в связке с реальным Catalog Service.

    POSTGRES_URL указывает на SQLite: движок тот же (SQLAlchemy),
    схема таблицы orders создаётся сервисом при старте.
    """
    db_path = os.path.join(tempfile.gettempdir(), "orders_e2e.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    svc = _start(
        "order_service", 8004,
        env={
            "POSTGRES_URL": f"sqlite:///{db_path}",
            "CATALOG_URL": "http://127.0.0.1:8002/api",
        },
    )
    yield svc
    svc.stop()
    if os.path.exists(db_path):
        os.remove(db_path)
