import os
from pathlib import Path


def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан: {path}")


# 1. События
events_py = """
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar
from uuid import uuid4
from booking.domain.models import BookingId, SeatId, UserId

@dataclass(frozen=True, slots=True)
class DomainEvent:
    routing_key: ClassVar[str]
    event_id: str
    occurred_at: datetime

    @staticmethod
    def new_id() -> str:
        return str(uuid4())

@dataclass(frozen=True, slots=True)
class BookingCreated(DomainEvent):
    routing_key: ClassVar[str] = "booking.created"
    booking_id: BookingId
    seat_id: SeatId
    user_id: UserId
    starts_at: datetime
    ends_at: datetime

@dataclass(frozen=True, slots=True)
class BookingCancelled(DomainEvent):
    routing_key: ClassVar[str] = "booking.cancelled"
    booking_id: BookingId
    seat_id: SeatId
    user_id: UserId
    starts_at: datetime
    ends_at: datetime

@dataclass(frozen=True, slots=True)
class BookingWithdrawn(DomainEvent):
    routing_key: ClassVar[str] = "booking.withdrawn"
    booking_id: BookingId
    seat_id: SeatId
    user_id: UserId
    starts_at: datetime
    ends_at: datetime
    reason: str
    withdrawn_by: UserId
"""
create_file("src/booking/domain/events.py", events_py)

# 2. Интерфейсы
event_bus_py = """
from typing import Protocol
from booking.domain.events import DomainEvent

class EventBus(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
"""
create_file("src/booking/ports/event_bus.py", event_bus_py)

# 3. Публикация
publisher_py = """
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
            headers={"event_type": type(event).__name__},
        )
        await exchange.publish(message, routing_key=event.routing_key)
        print(f"Published: {event.routing_key}")
"""
create_file("src/booking/adapters/rabbitmq_publisher.py", publisher_py)

# 4. Обработчик (заглушка, чтобы проверить работу)
worker_py = """
import asyncio
import json
import aio_pika
from booking.config import get_settings
from booking.adapters.rabbitmq_publisher import EXCHANGE

async def main():
    settings = get_settings()
    connection = await aio_pika.connect_robust(str(settings.broker_url))
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    queue = await channel.declare_queue("booking.notifications", durable=True)
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    await queue.bind(exchange, routing_key="booking.*")

    print("Worker started, waiting for messages...")

    async def process(message):
        body = json.loads(message.body)
        print(f"Received: {message.routing_key} -> {body.get('booking_id')}")
        await message.ack()

    await queue.consume(process)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
"""
create_file("src/booking/workers/notifier.py", worker_py)

# 5. Обновление сервиса (упрощённо, чтобы публиковать события)
service_py = """
from booking.domain.events import BookingCreated, DomainEvent
from booking.ports.event_bus import EventBus

class BookingService:
    def __init__(self, repository, clock, ids, policy, events: EventBus):
        self._repository = repository
        self._clock = clock
        self._ids = ids
        self._policy = policy
        self._events = events

    async def create(self, request):
        # ... проверки ...
        booking = ... # создание
        await self._repository.add(booking)
        await self._events.publish(
            BookingCreated(
                event_id=DomainEvent.new_id(),
                occurred_at=self._clock.now(),
                booking_id=booking.id,
                seat_id=booking.seat_id,
                user_id=booking.user_id,
                starts_at=booking.period.starts_at,
                ends_at=booking.period.ends_at,
            )
        )
        return booking
"""
create_file("src/booking/services/booking_service.py", service_py)

print("\n✅ Файлы для ЛР 6 созданы!")

