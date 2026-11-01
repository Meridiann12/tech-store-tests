import asyncio

from fastapi import FastAPI

from app import rabbitmq
from app.endpoints.order_router import router

app = FastAPI(title="Order Service")


@app.on_event("startup")
async def startup():
    # Создаём таблицы в БД (актуально при первом запуске)
    from app.database import Base, engine

    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Схема БД готова")
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] База данных недоступна: {exc}")

    # Подключаем обработчики очередей к основному циклу приложения

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(rabbitmq.consume(loop))


app.include_router(router, prefix="/api")
