from app.models.review import Review, ReviewCreate, ReviewStatus
from app.repositories.local_review_repo import ReviewRepo


class ReviewService:
    """Бизнес-логика отзывов."""

    def __init__(self, repo: ReviewRepo = None) -> None:
        self.repo = repo or ReviewRepo()

    def create_review(self, data: ReviewCreate) -> Review:
        # бизнес-правило: оценка товара - целое число от 1 до 5
        if not 1 <= data.rating <= 5:
            raise ValueError("Оценка должна быть целым числом от 1 до 5")
        review = Review(
            review_id=0,
            product_id=data.product_id,
            user_id=data.user_id,
            rating=data.rating,
            text=data.text,
        )
        return self.repo.create(review)

    def get_product_reviews(self, product_id: int) -> list[Review]:
        return [r for r in self.repo.get_reviews() if r.product_id == product_id]

    def moderate(self, review_id: int, approve: bool) -> Review:
        review = self.repo.get_by_id(review_id)
        review.status = ReviewStatus.APPROVED if approve else ReviewStatus.REJECTED
        return review

    def anonymize_user(self, user_id: int) -> int:
        return self.repo.anonymize_user(user_id)
