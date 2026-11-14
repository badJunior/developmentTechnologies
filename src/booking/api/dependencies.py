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
