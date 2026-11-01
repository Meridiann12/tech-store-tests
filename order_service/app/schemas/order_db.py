from sqlalchemy import Column, DateTime, Integer, JSON, Numeric, String

from app.database import Base


class OrderDB(Base):
    """ORM-схема таблицы orders в PostgreSQL."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="CREATED")
    items = Column(JSON, nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, nullable=False)
