import enum
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Review(BaseModel):
    """Анемичная модель отзыва. user_id = None после анонимизации
    (реакция на user.deleted)."""

    review_id: int
    product_id: int
    user_id: int | None
    rating: int
    text: str
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)


class ReviewCreate(BaseModel):
    product_id: int
    user_id: int
    rating: int
    text: str


class ModerateRequest(BaseModel):
    approve: bool = True
