import asyncio

from fastapi import FastAPI

from app import rabbitmq
from app.endpoints.review_router import router

app = FastAPI(title="Review Service")


@app.on_event("startup")
async def startup():
    # Подключаем обработчики очередей к основному циклу приложения

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(rabbitmq.consume(loop))


app.include_router(router, prefix="/api")
