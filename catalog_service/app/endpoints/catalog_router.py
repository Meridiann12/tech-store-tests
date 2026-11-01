from fastapi import APIRouter, Depends, HTTPException

from app.models.product import Product, ProductCreate, ProductUpdate
from app.rabbitmq import publish_event
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/products", tags=["Products"])


def get_service() -> CatalogService:
    return CatalogService()


@router.post("", response_model=Product, status_code=201, summary="Добавить товар")
async def create_product(data: ProductCreate, service: CatalogService = Depends(get_service)) -> Product:
    """Создаёт товар и публикует product.created
    (Inventory создаст запись остатка с нулевым количеством)."""
    product = service.create_product(data)
    await publish_event(
        "catalog",
        "topic",
        "product.created",
        {
            "event": "product.created",
            "product_id": product.id,
            "name": product.name,
            "category_id": product.category_id,
            "price": product.price,
        },
    )
    return product


@router.get("/{product_id}", response_model=Product, summary="Получить товар")
def get_product(product_id: int, service: CatalogService = Depends(get_service)) -> Product:
    """Этот эндпоинт вызывает Order Service по HTTP (requests),
    чтобы получить актуальные цену и название товара при оформлении заказа."""
    try:
        return service.get_product(product_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.put("/{product_id}", response_model=Product, summary="Обновить товар")
async def update_product(product_id: int, data: ProductUpdate, service: CatalogService = Depends(get_service)) -> Product:
    """Обновляет товар и публикует product.updated."""
    try:
        product = service.update_product(product_id, data)
    except KeyError as exc:
        raise HTTPException(404, str(exc))

    await publish_event(
        "catalog",
        "topic",
        "product.updated",
        {
            "event": "product.updated",
            "product_id": product.id,
            "changed_fields": [k for k, v in data.model_dump().items() if v is not None],
            "new_price": product.price,
        },
    )
    return product
