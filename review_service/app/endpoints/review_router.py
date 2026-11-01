from fastapi import APIRouter, Depends, HTTPException

from app.models.review import ModerateRequest, Review, ReviewCreate
from app.rabbitmq import publish_event
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def get_service() -> ReviewService:
    return ReviewService()


@router.post("", response_model=Review, status_code=201, summary="Оставить отзыв")
async def create_review(data: ReviewCreate, service: ReviewService = Depends(get_service)) -> Review:
    """Создаёт отзыв и публикует review.created
    (Catalog Service пересчитает средний рейтинг товара)."""
    try:
        review = service.create_review(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    await publish_event(
        "reviews",
        "topic",
        "review.created",
        {
            "event": "review.created",
            "review_id": review.review_id,
            "product_id": review.product_id,
            "user_id": review.user_id,
            "rating": review.rating,
            "text": review.text,
        },
    )
    return review


@router.get("/product/{product_id}", response_model=list[Review], summary="Отзывы на товар")
def get_product_reviews(product_id: int, service: ReviewService = Depends(get_service)) -> list[Review]:
    return service.get_product_reviews(product_id)


@router.post("/{review_id}/moderate", response_model=Review, summary="Модерация отзыва")
async def moderate(review_id: int, data: ModerateRequest, service: ReviewService = Depends(get_service)) -> Review:
    """Модерирует отзыв и публикует review.moderated
    в fanout-обменник notifications (уведомление клиенту)."""
    try:
        review = service.moderate(review_id, data.approve)
    except KeyError as exc:
        raise HTTPException(404, str(exc))

    await publish_event(
        "notifications",
        "fanout",
        "",
        {
            "event": "review.moderated",
            "review_id": review.review_id,
            "status": review.status.value,
            "user_id": review.user_id,
        },
    )
    return review
