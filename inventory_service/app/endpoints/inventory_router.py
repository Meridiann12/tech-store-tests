from fastapi import APIRouter, Depends, HTTPException

from app.models.stock import StockItem, SupplyRequest
from app.rabbitmq import publish_event
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def get_service() -> InventoryService:
    return InventoryService()


@router.get("", response_model=list[StockItem], summary="Все остатки склада")
def get_all_stocks(service: InventoryService = Depends(get_service)) -> list[StockItem]:
    return service.get_all()


@router.get("/{product_id}", response_model=StockItem, summary="Остаток товара")
def get_stock(product_id: int, service: InventoryService = Depends(get_service)) -> StockItem:
    try:
        return service.get_stock(product_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.post("/{product_id}/supply", response_model=StockItem, summary="Приёмка товара")
async def supply(product_id: int, data: SupplyRequest, service: InventoryService = Depends(get_service)) -> StockItem:
    """Принимает товар на склад. Если после приёмки остаток ниже порога,
    публикует inventory.low_stock в fanout-обменник notifications."""
    try:
        item = service.supply(product_id, data.amount)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    if service.is_low_stock(item):
        await publish_event(
            "notifications",
            "fanout",
            "",
            {
                "event": "inventory.low_stock",
                "product_id": product_id,
                "current_stock": item.quantity,
                "threshold": item.threshold,
            },
        )
    return item
