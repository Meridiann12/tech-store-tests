from fastapi import APIRouter, Depends, HTTPException

from app.models.payment import Payment
from app.rabbitmq import publish_event
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_service() -> PaymentService:
    return PaymentService()


@router.post("/{order_id}/pay", response_model=Payment, summary="Оплатить заказ")
async def pay(order_id: int, service: PaymentService = Depends(get_service)) -> Payment:
    """Проводит платёж и публикует payment.completed или payment.failed
    (при превышении лимита 200 000 руб.) в обменник payments."""
    try:
        payment = service.pay(order_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    if payment.status.value == "PAID":
        await publish_event(
            "payments",
            "topic",
            "payment.completed",
            {
                "event": "payment.completed",
                "order_id": payment.order_id,
                "payment_id": payment.payment_id,
                "amount": payment.amount,
                "status": "PAID",
            },
        )
    else:
        await publish_event(
            "payments",
            "topic",
            "payment.failed",
            {
                "event": "payment.failed",
                "order_id": payment.order_id,
                "payment_id": payment.payment_id,
                "amount": payment.amount,
                "status": "FAILED",
                "reason": "insufficient_funds",
            },
        )
    return payment


@router.get("/{order_id}", response_model=Payment, summary="Статус платежа по заказу")
def get_payment(order_id: int, service: PaymentService = Depends(get_service)) -> Payment:
    try:
        return service.get_payment(order_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.get("", response_model=list[Payment], summary="Все транзакции")
def get_payments(service: PaymentService = Depends(get_service)) -> list[Payment]:
    return service.get_payments()
