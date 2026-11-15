import os
from pathlib import Path


def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан/обновлен: {path}")


# 1. События
create_file("src/booking/domain/events.py", """
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
""")

# 2. Интерфейс EventBus
create_file("src/booking/ports/event_bus.py", """
from typing import Protocol
from booking.domain.events import DomainEvent

class EventBus(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
""")

# 3. Публикатор
create_file("src/booking/adapters/rabbitmq_publisher.py", """
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
""")

# 4. Сервис с BookingPolicy
create_file("src/booking/services/booking_service.py", """
from dataclasses import dataclass
from datetime import timedelta
from collections.abc import Callable

import structlog

from booking.domain import rules
from booking.domain.errors import SeatAlreadyBooked
from booking.domain.models import Booking, BookingRequest, SeatKind
from booking.domain.rules import WorkingHours
from booking.domain.events import BookingCreated, DomainEvent
from booking.ports.clock import Clock, IdGenerator
from booking.ports.event_bus import EventBus
from booking.ports.repository import BookingRepository


@dataclass(frozen=True, slots=True)
class BookingPolicy:
    working_hours: WorkingHours
    max_duration: timedelta


PolicyFor = Callable[[SeatKind], BookingPolicy]


class BookingService:
    def __init__(
        self,
        repository: BookingRepository,
        clock: Clock,
        ids: IdGenerator,
        policy_for: PolicyFor,
        events: EventBus,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._ids = ids
        self._policy_for = policy_for
        self._events = events

    async def create(self, request: BookingRequest) -> Booking:
        kind = SeatKind.MEETING_ROOM if str(request.seat_id).startswith("room") else SeatKind.DESK
        policy = self._policy_for(kind)
        now = self._clock.now()

        rules.require_valid_period(request)
        rules.require_within_working_hours(request, policy.working_hours)
        rules.require_duration_at_most(request, policy.max_duration)
        rules.require_not_in_past(request, now)

        if await self._repository.find_overlapping(request.seat_id, request.period):
            raise SeatAlreadyBooked(f"seat {request.seat_id} is taken")

        booking = Booking(
            id=self._ids.next_id(),
            seat_id=request.seat_id,
            user_id=request.user_id,
            period=request.period,
        )
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

        structlog.get_logger().info("booking_created", booking_id=booking.id)
        return booking
""")

# 5. Политики
create_file("src/booking/services/policies.py", """
from datetime import time, timedelta
from booking.domain.rules import WorkingHours
from booking.services.booking_service import BookingPolicy

DESK_POLICY = BookingPolicy(WorkingHours(), timedelta(hours=8))
ROOM_POLICY = BookingPolicy(WorkingHours(time(9), time(20)), timedelta(hours=3))

def policy_for(kind) -> BookingPolicy:
    return ROOM_POLICY if kind == "meeting_room" else DESK_POLICY
""")

# 6. Зависимости
create_file("src/booking/api/dependencies.py", """
from fastapi import Depends
from typing import Annotated
from booking.config import Settings, get_settings
from booking.adapters.in_memory_repository import InMemoryBookingRepository
from booking.adapters.system_clock import SystemClock, UuidIdGenerator
from booking.adapters.rabbitmq_publisher import RabbitMqEventBus
from booking.services.booking_service import BookingService
from booking.services.policies import policy_for

_repo = InMemoryBookingRepository()

async def get_booking_service(settings: Annotated[Settings, Depends(get_settings)]) -> BookingService:
    return BookingService(
        repository=_repo,
        clock=SystemClock(),
        ids=UuidIdGenerator(),
        policy_for=policy_for,
        events=RabbitMqEventBus(str(settings.broker_url)),
    )
""")

# 7. Обновление настроек
config_py = """
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, PostgresDsn, SecretStr, AmqpDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["debug", "info", "warning", "error"]
Environment = Literal["development", "test", "production"]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    port: int = Field(default=8080, ge=1, le=65535)
    log_level: LogLevel = "info"
    environment: Environment = "development"
    app_version: str = "0.0.0-dev"

    database_url: PostgresDsn
    jwt_secret: SecretStr
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    broker_url: AmqpDsn
    cache_url: RedisDsn

@lru_cache
def get_settings() -> Settings:
    return Settings()
"""
create_file("src/booking/config.py", config_py)

# 8. Обновление .env
env_path = Path(".env")
if env_path.exists():
    content = env_path.read_text(encoding="utf-8")
    if "BROKER_URL" not in content:
        content += "\nBROKER_URL=amqp://booking:booking@localhost:5672/\n"
    if "CACHE_URL" not in content:
        content += "CACHE_URL=redis://localhost:6379/0\n"
    env_path.write_text(content, encoding="utf-8")
    print("Обновлен .env")
else:
    create_file(".env", """
DATABASE_URL=postgresql://booking:booking@localhost:5433/booking
JWT_SECRET=super-secret-key-change-me
BROKER_URL=amqp://booking:booking@localhost:5672/
CACHE_URL=redis://localhost:6379/0
""")

# 9. Обработчик (worker)
create_file("src/booking/workers/notifier.py", """
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
""")

print("\n✅ Все файлы для ЛР 6 обновлены!")
print("Теперь выполните в терминале:")
print("uv add aio-pika redis")
print("docker compose up -d --build")