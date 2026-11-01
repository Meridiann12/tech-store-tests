import asyncio
import json
import traceback

from aio_pika import DeliveryMode, ExchangeType, IncomingMessage, Message, connect_robust

from app.services.catalog_service import CatalogService
from app.settings import settings


async def publish_event(exchange_name: str, exchange_type: str, routing_key: str, payload: dict) -> None:
    """Публикация события в обменник RabbitMQ."""
    try:
        connection = await connect_robust(settings.amqp_url)
    except Exception:  # noqa: BLE001
        print("[WARN] RabbitMQ недоступен, событие не отправлено:", routing_key)
        return

    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            exchange_name, ExchangeType(exchange_type), durable=True
        )
        message = Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=routing_key)
        print(f"[PUBLISHED] {exchange_name} :: {routing_key}")
    finally:
        await connection.close()


async def _process_review_created(msg: IncomingMessage):
    """Обработка review.created: пересчёт среднего рейтинга товара."""
    try:
        data = json.loads(msg.body.decode())
        print("[RECEIVED] review.created:", data)

        CatalogService().apply_review_rating(int(data["product_id"]), float(data["rating"]))

        await msg.ack()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        await msg.nack()


async def consume(loop) -> None:
    # если брокер ещё поднимается - ждём и повторяем попытку
    while True:
        try:
            connection = await connect_robust(settings.amqp_url)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] RabbitMQ недоступен ({exc.__class__.__name__}), повтор через 5 с")
            await asyncio.sleep(5)

    channel = await connection.channel()

    # catalog_queue: auto_delete=True - пересчёт рейтинга не критичен при потере
    reviews_exchange = await channel.declare_exchange(
        "reviews", ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue("catalog_queue", auto_delete=True)
    await queue.bind(reviews_exchange, routing_key="review.created")
    await queue.consume(_process_review_created)

    print("Started RabbitMQ consuming...")
    return connection
