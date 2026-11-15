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
