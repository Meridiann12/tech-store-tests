from app.models.payment import Payment, PaymentStatus
from app.repositories.local_payment_repo import PaymentRepo

# бизнес-правило: платежи свыше лимита отклоняются
PAYMENT_LIMIT = 200000.0


class PaymentService:
    """Бизнес-логика платежей."""

    def __init__(self, repo: PaymentRepo = None) -> None:
        self.repo = repo or PaymentRepo()

    def get_payment(self, order_id: int) -> Payment:
        return self.repo.get_by_order(order_id)

    def get_payments(self) -> list[Payment]:
        return self.repo.get_payments()

    def create_transaction(self, order_id: int, amount: float) -> Payment:
        """Реакция на order.created: создать транзакцию и ждать оплату."""
        try:
            return self.repo.get_by_order(order_id)
        except KeyError:
            return self.repo.create(order_id, amount)

    def pay(self, order_id: int) -> Payment:
        """Проведение платежа по заказу.

        Бизнес-правило: если сумма превышает PAYMENT_LIMIT,
        платёж отклоняется (payment.failed).
        """
        payment = self.repo.get_by_order(order_id)
        if payment.status != PaymentStatus.PENDING:
            raise ValueError(
                f"Транзакция заказа {order_id} в статусе {payment.status.value}, оплата невозможна"
            )
        if payment.amount > PAYMENT_LIMIT:
            payment.status = PaymentStatus.FAILED
        else:
            payment.status = PaymentStatus.PAID
        return payment

    def refund_if_paid(self, order_id: int) -> Payment | None:
        """Реакция на order.cancelled: возврат, если оплата уже прошла."""
        try:
            payment = self.repo.get_by_order(order_id)
        except KeyError:
            return None
        if payment.status == PaymentStatus.PAID:
            payment.status = PaymentStatus.REFUNDED
            return payment
        return None
