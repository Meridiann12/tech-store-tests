from app.models.payment import Payment

# локальное хранилище: список объектов в памяти процесса
_payments: list[Payment] = []
_next_id = 555  # идентификаторы начинаются с 555 - как в примерах отчёта ПР N5


class PaymentRepo:
    def get_payments(self) -> list[Payment]:
        return _payments

    def get_by_order(self, order_id: int) -> Payment:
        for payment in _payments:
            if payment.order_id == order_id:
                return payment
        raise KeyError(f"Payment for order {order_id} not found")

    def create(self, order_id: int, amount: float) -> Payment:
        global _next_id
        payment = Payment(payment_id=_next_id, order_id=order_id, amount=amount)
        _next_id += 1
        _payments.append(payment)
        return payment
