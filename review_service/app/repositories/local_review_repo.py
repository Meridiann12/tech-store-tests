from app.models.review import Review

# локальное хранилище: список объектов в памяти процесса
_reviews: list[Review] = []
_next_id = 9001  # идентификаторы начинаются с 9001 - как в примерах отчёта ПР N5


class ReviewRepo:
    def get_reviews(self) -> list[Review]:
        return _reviews

    def get_by_id(self, review_id: int) -> Review:
        for review in _reviews:
            if review.review_id == review_id:
                return review
        raise KeyError(f"Review {review_id} not found")

    def create(self, review: Review) -> Review:
        global _next_id
        review.review_id = _next_id
        _next_id += 1
        _reviews.append(review)
        return review

    def anonymize_user(self, user_id: int) -> int:
        # храним историю отзывов, но без персональных данных
        count = 0
        for review in _reviews:
            if review.user_id == user_id:
                review.user_id = None
                count += 1
        return count
