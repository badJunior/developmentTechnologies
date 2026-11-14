import json
from dataclasses import asdict
from datetime import datetime
import aio_pika
from booking.domain.events import DomainEvent

EXCHANGE = "booking.events"

class RabbitMqEventBus:
    def __init__(self, url: str) -> None:
        self._url = url
        self._connection = None
        self._exchange = None

    async def _ensure_exchange(self):
        if self._exchange is None:
            self._connection = await aio_pika.connect_robust(self._url)
            channel = await self._connection.channel()
            self._exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        return self._exchange

    async def publish(self, event: DomainEvent) -> None:
        exchange = await self._ensure_exchange()
        payload = {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in asdict(event).items()
        }
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            message_id=event.event_id,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=event.routing_key)
        print(f"Published: {event.routing_key}")
