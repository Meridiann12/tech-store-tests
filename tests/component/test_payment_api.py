"""Компонентные тесты Payment Service: http://127.0.0.1:8005/api/payments.

Транзакция создаётся консьюмером по событию order.created (RabbitMQ);
в изолированном прогоне компонентных тестов брокер не поднимается,
поэтому через HTTP проверяется контракт ошибок 404.
Позитивные ветки оплаты покрыты unit-тестами Payment Service.
"""
import requests


def test_get_unknown_payment_404(payment_svc):
    assert requests.get(f"{payment_svc.base}/payments/424242").status_code == 404


def test_pay_unknown_order_404(payment_svc):
    resp = requests.post(f"{payment_svc.base}/payments/424242/pay")
    assert resp.status_code == 404


def test_payments_list_empty(payment_svc):
    """GET /api/payments возвращает JSON-массив."""
    resp = requests.get(f"{payment_svc.base}/payments")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
