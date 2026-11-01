from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order, OrderCreate
from app.rabbitmq import publish_event
from app.repositories.db_order_repo import OrderRepo
from app.services.order_service import CatalogUnavailableError, OrderService, ProductNotFoundError


def get_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(OrderRepo(db))


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=Order, status_code=201, summary="Создать заказ")
async def create_order(data: OrderCreate, service: OrderService = Depends(get_service)) -> Order:
    """Оформляет заказ: получает цены через HTTP-вызов Catalog Service,
    сохраняет заказ в PostgreSQL и публикует order.created
    (Inventory резервирует товар, Payment создаёт транзакцию)."""
    try:
        order = service.create_order(data)
    except ProductNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except CatalogUnavailableError as exc:
        raise HTTPException(503, str(exc))

    await publish_event(
        "orders",
        "topic",
        "order.created",
        {
            "event": "order.created",
            "order_id": order.id,
            "user_id": order.user_id,
            "items": [item.model_dump() for item in order.items],
            "total_price": order.total_price,
        },
    )
    return order


@router.get("/{order_id}", response_model=Order, summary="Получить заказ")
def get_order(order_id: int, service: OrderService = Depends(get_service)) -> Order:
    try:
        return service.get_order(order_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.post("/{order_id}/cancel", response_model=Order, summary="Отменить заказ")
async def cancel_order(order_id: int, service: OrderService = Depends(get_service)) -> Order:
    """Отменяет заказ и публикует order.cancelled
    (Inventory снимет резерв, Payment вернёт средства, если оплатили)."""
    try:
        order = service.cancel_order(order_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))

    await publish_event(
        "orders",
        "topic",
        "order.cancelled",
        {"event": "order.cancelled", "order_id": order.id, "reason": "user_request", "items": [item.model_dump() for item in order.items]},
    )
    return order
