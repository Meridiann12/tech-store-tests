from app.models.product import Product

# локальное хранилище: список объектов в памяти процесса
_products: list[Product] = []
_next_id = 501  # идентификаторы начинаются с 501 - как в примерах отчёта ПР N5


class ProductRepo:
    def get_products(self) -> list[Product]:
        return _products

    def get_by_id(self, product_id: int) -> Product:
        for product in _products:
            if product.id == product_id:
                return product
        raise KeyError(f"Product {product_id} not found")

    def create_product(self, product: Product) -> Product:
        global _next_id
        product.id = _next_id
        _next_id += 1
        _products.append(product)
        return product

    def update(self, product_id: int, name: str | None, price: float | None) -> Product:
        product = self.get_by_id(product_id)
        if name is not None:
            product.name = name
        if price is not None:
            product.price = price
        return product

    def apply_rating(self, product_id: int, rating: float) -> Product:
        product = self.get_by_id(product_id)
        product.rating_sum += rating
        product.reviews_count += 1
        product.rating = round(product.rating_sum / product.reviews_count, 2)
        return product
