from app.models.stock import StockItem

# локальное хранилище: список объектов в памяти процесса
_stocks: list[StockItem] = []


class StockRepo:
    def get_all(self) -> list[StockItem]:
        return _stocks

    def get_by_product(self, product_id: int) -> StockItem:
        for item in _stocks:
            if item.product_id == product_id:
                return item
        raise KeyError(f"Stock for product {product_id} not found")

    def create(self, product_id: int) -> StockItem:
        item = StockItem(product_id=product_id)
        _stocks.append(item)
        return item
