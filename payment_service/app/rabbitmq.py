import asyncio
import json
import traceback

from aio_pika import DeliveryMode, ExchangeType, IncomingMessage, Message, connect_robust

from app.services.payment_service import PaymentService
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


def _payload(payment, status: str, reason: str | None = None) -> dict:
    data = {
        "event": f"payment.{status.lower()}",
        "order_id": payment.order_id,
        "payment_id": payment.payment_id,
        "amount": payment.amount,
        "status": status,
    }
    if reason:
        data["reason"] = reason
    return data


async def _process_event(msg: IncomingMessage):
    """Вызов нужного метода сервиса в зависимости от routing_key."""
    try:
        data = json.loads(msg.body.decode())
        routing_key = msg.routing_key
        print("[RECEIVED]", routing_key)

        if routing_key == "order.created":
            # инициируем создание транзакции и ожидание оплаты
            PaymentService().create_transaction(
                int(data["order_id"]), float(data["total_price"])
            )
        elif routing_key == "order.cancelled":
            # если оплата уже прошла - инициируем возврат средств
            payment = PaymentService().refund_if_paid(int(data["order_id"]))
            if payment is not None:
                await publish_event(
                    "payments", "topic", "payment.refunded",
                    _payload(payment, "REFUNDED"),
                )
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

    # payment_queue: durable, слушает обменник orders
    orders_exchange = await channel.declare_exchange("orders", ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("payment_queue", durable=True)
    await queue.bind(orders_exchange, routing_key="order.created")
    await queue.bind(orders_exchange, routing_key="order.cancelled")
    await queue.consume(_process_event)

    print("Started RabbitMQ consuming...")
    return connection
