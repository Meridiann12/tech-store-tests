from pydantic import BaseModel


class StockItem(BaseModel):
    """Остаток товара на складе: доступно / зарезервировано под заказы."""

    product_id: int
    quantity: int = 0
    reserved: int = 0
    threshold: int = 5  # бизнес-правило: ниже этого значения - низкий остаток


class SupplyRequest(BaseModel):
    amount: int
