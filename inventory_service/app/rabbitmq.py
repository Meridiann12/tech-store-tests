import asyncio
import json
import traceback

from aio_pika import DeliveryMode, ExchangeType, IncomingMessage, Message, connect_robust

from app.services.inventory_service import InventoryService
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


async def _process_event(msg: IncomingMessage):
    """Вызов нужного метода сервиса в зависимости от routing_key."""
    try:
        data = json.loads(msg.body.decode())
        routing_key = msg.routing_key
        print("[RECEIVED]", routing_key)

        if routing_key == "order.created":
            # резервируем товар под заказ
            result = InventoryService().reserve_for_order(
                int(data["order_id"]), data["items"]
            )
            if result["status"] == "reserved":
                await publish_event(
                    "inventory", "topic", "inventory.reserved",
                    {
                        "event": "inventory.reserved",
                        "order_id": result["order_id"],
                        "reserved_items": result["reserved_items"],
                    },
                )
            else:
                await publish_event(
                    "inventory", "topic", "inventory.failed",
                    {
                        "event": "inventory.failed",
                        "order_id": result["order_id"],
                        "missing_products": result["missing_products"],
                    },
                )
        elif routing_key == "order.cancelled":
            # снимаем резерв с товаров
            InventoryService().release_reserve(int(data["order_id"]), data.get("items", []))
        elif routing_key == "product.created":
            # создаём начальную запись остатка для нового товара (0 единиц)
            InventoryService().create_initial_stock(int(data["product_id"]))
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

    # inventory_queue: durable, слушает обменники orders и catalog
    orders_exchange = await channel.declare_exchange("orders", ExchangeType.TOPIC, durable=True)
    catalog_exchange = await channel.declare_exchange("catalog", ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("inventory_queue", durable=True)
    await queue.bind(orders_exchange, routing_key="order.created")
    await queue.bind(orders_exchange, routing_key="order.cancelled")
    await queue.bind(catalog_exchange, routing_key="product.created")
    await queue.consume(_process_event)

    print("Started RabbitMQ consuming...")
    return connection
