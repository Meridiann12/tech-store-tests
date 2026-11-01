from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order_db import OrderDB


class OrderRepo:
    """Репозиторий заказов: хранение в PostgreSQL.

    Внешний интерфейс тот же, что у локального репозитория из методички,
    поэтому сервисный слой не меняется при смене источника данных.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_orders(self) -> list[Order]:
        return [self._to_model(row) for row in self.db.query(OrderDB).all()]

    def get_by_id(self, order_id: int) -> Order:
        return self._to_model(self._get_row(order_id))

    def create_order(self, order: Order) -> Order:
        row = OrderDB(
            user_id=order.user_id,
            status=order.status.value,
            items=[item.model_dump() for item in order.items],
            total_price=order.total_price,
            created_at=order.created_at,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_model(row)

    def change_status(self, order_id: int, status: OrderStatus) -> Order:
        row = self._get_row(order_id)
        row.status = status.value
        self.db.commit()
        self.db.refresh(row)
        return self._to_model(row)

    def anonymize_user(self, user_id: int) -> int:
        # реакция на user.deleted: обезличиваем заказы пользователя
        rows = self.db.query(OrderDB).filter(OrderDB.user_id == user_id).all()
        for row in rows:
            row.user_id = 0
        self.db.commit()
        return len(rows)

    def _get_row(self, order_id: int) -> OrderDB:
        row = self.db.query(OrderDB).filter(OrderDB.id == order_id).first()
        if row is None:
            raise KeyError(f"Order {order_id} not found")
        return row

    @staticmethod
    def _to_model(row: OrderDB) -> Order:
        return Order(
            id=row.id,
            user_id=row.user_id,
            status=OrderStatus(row.status),
            items=[
                OrderItem(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item.get("price"),
                    name=item.get("name"),
                )
                for item in row.items
            ],
            total_price=float(row.total_price),
            created_at=row.created_at,
        )
