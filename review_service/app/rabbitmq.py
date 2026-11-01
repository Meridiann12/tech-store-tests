import asyncio
import json
import traceback

from aio_pika import DeliveryMode, ExchangeType, IncomingMessage, Message, connect_robust

from app.services.review_service import ReviewService
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


async def _process_user_deleted(msg: IncomingMessage):
    """Обработка user.deleted: анонимизация отзывов пользователя."""
    try:
        data = json.loads(msg.body.decode())
        print("[RECEIVED] user.deleted:", data)

        ReviewService().anonymize_user(int(data["user_id"]))

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

    # review_queue: durable, слушает обменник users
    users_exchange = await channel.declare_exchange("users", ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("review_queue", durable=True)
    await queue.bind(users_exchange, routing_key="user.deleted")
    await queue.consume(_process_user_deleted)

    print("Started RabbitMQ consuming...")
    return connection
