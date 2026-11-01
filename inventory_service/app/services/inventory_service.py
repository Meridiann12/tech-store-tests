from app.models.stock import StockItem
from app.repositories.local_stock_repo import StockRepo


class InventoryService:
    """Бизнес-логика склада: приёмка товара, резервы под заказы."""

    def __init__(self, repo: StockRepo = None) -> None:
        self.repo = repo or StockRepo()

    def get_all(self) -> list[StockItem]:
        return self.repo.get_all()

    def get_stock(self, product_id: int) -> StockItem:
        return self.repo.get_by_product(product_id)

    def create_initial_stock(self, product_id: int) -> StockItem:
        """Реакция на product.created: начальная запись остатка (0 единиц)."""
        try:
            return self.repo.get_by_product(product_id)
        except KeyError:
            return self.repo.create(product_id)

    def supply(self, product_id: int, amount: int) -> StockItem:
        """Приёмка товара на склад."""
        if amount <= 0:
            raise ValueError("Количество должно быть положительным")
        try:
            item = self.repo.get_by_product(product_id)
        except KeyError:
            item = self.repo.create(product_id)
        item.quantity += amount
        return item

    def reserve_for_order(self, order_id: int, items: list[dict]) -> dict:
        """Резерв товара под заказ.

        Бизнес-правило: резерв возможен, только если доступного остатка
        хватает на все позиции заказа. Возвращает результат для публикации
        события inventory.reserved или inventory.failed.
        """
        requested = []
        missing = []
        for line in items:
            product_id = int(line["product_id"])
            quantity = int(line["quantity"])
            requested.append({"product_id": product_id, "quantity": quantity})
            try:
                stock = self.repo.get_by_product(product_id)
            except KeyError:
                missing.append(
                    {"product_id": product_id, "requested": quantity, "available": 0}
                )
                continue
            available = stock.quantity - stock.reserved
            if available < quantity:
                missing.append(
                    {"product_id": product_id, "requested": quantity, "available": available}
                )

        if missing:
            return {"status": "failed", "order_id": order_id, "missing_products": missing}

        for line in requested:
            stock = self.repo.get_by_product(line["product_id"])
            stock.reserved += line["quantity"]
        return {"status": "reserved", "order_id": order_id, "reserved_items": requested}

    def release_reserve(self, order_id: int, items: list[dict]) -> None:
        """Реакция на order.cancelled: снять резерв с товаров."""
        for line in items:
            try:
                stock = self.repo.get_by_product(int(line["product_id"]))
            except KeyError:
                continue
            stock.reserved = max(0, stock.reserved - int(line["quantity"]))

    def is_low_stock(self, item: StockItem) -> bool:
        return item.quantity < item.threshold
