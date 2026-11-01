from app.models.product import Product, ProductCreate, ProductUpdate
from app.repositories.local_product_repo import ProductRepo


class CatalogService:
    """Бизнес-логика каталога. Не знает, где хранятся данные."""

    def __init__(self, repo: ProductRepo = None) -> None:
        self.repo = repo or ProductRepo()

    def create_product(self, data: ProductCreate) -> Product:
        return self.repo.create_product(Product(**data.model_dump()))

    def get_product(self, product_id: int) -> Product:
        return self.repo.get_by_id(product_id)

    def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        return self.repo.update(product_id, data.name, data.price)

    def apply_review_rating(self, product_id: int, rating: float) -> Product:
        # реакция на review.created: пересчитать средний рейтинг товара
        return self.repo.apply_rating(product_id, rating)
