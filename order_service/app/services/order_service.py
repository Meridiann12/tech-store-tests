from datetime import datetime

import requests

from app.models.order import Order, OrderCreate, OrderStatus
from app.repositories.db_order_repo import OrderRepo
from app.settings import settings


class ProductNotFoundError(Exception):
    pass


class CatalogUnavailableError(Exception):
    pass


class OrderService:
    """Бизнес-логика заказов.

    Не знает, где хранятся данные (работает через репозиторий) и откуда
    приходят товары: Catalog Service вызывается синхронно по HTTP.
    """

    def __init__(self, repo: OrderRepo) -> None:
        self.repo = repo

    def get_order(self, order_id: int) -> Order:
        return self.repo.get_by_id(order_id)

    def create_order(self, data: OrderCreate) -> Order:
        # цены товаров получаем из Catalog Service по HTTP (requests)
        items = []
        total_price = 0.0
        for line in data.items:
            product = self._fetch_product(line.product_id)
            items.append(
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "price": product["price"],
                    "name": product["name"],
                }
            )
            total_price += product["price"] * line.quantity

        order = Order(
            id=0,
            user_id=data.user_id,
            status=OrderStatus.CREATED,
            items=items,
            total_price=round(total_price, 2),
            created_at=datetime.now(),
        )
        return self.repo.create_order(order)

    def cancel_order(self, order_id: int) -> Order:
        order = self.repo.get_by_id(order_id)
        if order.status == OrderStatus.PAID:
            # оплаченный заказ сразу не отменяем: payment.refunded
            # вернёт его в статус RETURNED
            return order
        return self.repo.change_status(order_id, OrderStatus.CANCELLED)

    def change_status(self, order_id: int, status: OrderStatus) -> Order:
        """Обработка входящих событий inventory.* и payment.*."""
        return self.repo.change_status(order_id, status)

    def anonymize_user(self, user_id: int) -> int:
        """Реакция на user.deleted: обезличить заказы пользователя."""
        return self.repo.anonymize_user(user_id)

    def _fetch_product(self, product_id: int) -> dict:
        # синхронное межсервисное взаимодействие: HTTP-запрос к Catalog Service
        url = f"{settings.catalog_url}/products/{product_id}"
        try:
            response = requests.get(url, timeout=5)
        except requests.RequestException:
            raise CatalogUnavailableError(f"Catalog Service недоступен: {url}")
        if response.status_code == 404:
            raise ProductNotFoundError(f"Товар {product_id} не найден в каталоге")
        response.raise_for_status()
        return response.json()
