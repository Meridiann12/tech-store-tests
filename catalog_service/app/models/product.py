from datetime import datetime

from pydantic import BaseModel, Field


class Product(BaseModel):
    """Анемичная модель товара каталога."""

    id: int = 0  # назначается репозиторием при создании
    name: str
    category_id: int
    price: float
    rating: float = 0.0
    rating_sum: float = 0.0
    reviews_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class ProductCreate(BaseModel):
    name: str
    category_id: int
    price: float


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
