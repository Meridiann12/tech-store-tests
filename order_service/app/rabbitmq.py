import asyncio
import json
import traceback

from aio_pika import (
    DeliveryMode,
    ExchangeType,
    IncomingMessage,
    Message,
    connect_robust,
)

from app.database import SessionLocal
from app.models.order import OrderStatus
from app.repositories.db_order_repo import OrderRepo
from app.services.order_service import OrderService
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


def _service() -> OrderService:
    """Сервисный слой с репозиторием, привязанным к новой сессии БД."""
    return OrderService(OrderRepo(SessionLocal()))


async def _process_event(msg: IncomingMessage):
    """Обработка входящих событий inventory.* / payment.* / user.deleted."""
    try:
        data = json.loads(msg.body.decode())
        routing_key = msg.routing_key
        print("[RECEIVED]", routing_key)

        with SessionLocal() as db:
            service = OrderService(OrderRepo(db))

            if routing_key == "inventory.reserved":
                service.change_status(int(data["order_id"]), OrderStatus.READY_FOR_PAYMENT)
            elif routing_key == "inventory.failed":
                service.change_status(int(data["order_id"]), OrderStatus.CANCELLED)
            elif routing_key == "payment.completed":
                service.change_status(int(data["order_id"]), OrderStatus.PAID)
            elif routing_key == "payment.failed":
                service.change_status(int(data["order_id"]), OrderStatus.CANCELLED)
            elif routing_key == "payment.refunded":
                service.change_status(int(data["order_id"]), OrderStatus.RETURNED)
            elif routing_key == "user.deleted":
                service.anonymize_user(int(data["user_id"]))
            else:
                print("[WARN] Неизвестное сообщение:", routing_key)

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

    # order_queue: durable, слушает обменники inventory, payments и users
    inventory_exchange = await channel.declare_exchange("inventory", ExchangeType.TOPIC, durable=True)
    payments_exchange = await channel.declare_exchange("payments", ExchangeType.TOPIC, durable=True)
    users_exchange = await channel.declare_exchange("users", ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("order_queue", durable=True)
    await queue.bind(inventory_exchange, routing_key="inventory.reserved")
    await queue.bind(inventory_exchange, routing_key="inventory.failed")
    await queue.bind(payments_exchange, routing_key="payment.completed")
    await queue.bind(payments_exchange, routing_key="payment.failed")
    await queue.bind(payments_exchange, routing_key="payment.refunded")
    await queue.bind(users_exchange, routing_key="user.deleted")
    await queue.consume(_process_event)

    print("Started RabbitMQ consuming...")
    return connection
