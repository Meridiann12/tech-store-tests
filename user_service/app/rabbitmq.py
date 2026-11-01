import json

from aio_pika import DeliveryMode, ExchangeType, Message, connect_robust

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


async def consume(loop) -> None:
    """User Service только публикует события, входящие очереди не слушает."""
    print("User Service: входящие очереди не требуются, работаем только на публикацию")
    return None
