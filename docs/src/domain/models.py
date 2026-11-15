from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import NewType

BookingId = NewType("BookingId", str)
SeatId = NewType("SeatId", str)
UserId = NewType("UserId", str)

class SeatKind(StrEnum):
    DESK = "desk"
    MEETING_ROOM = "meeting_room"

@dataclass(frozen=True, slots=True)
class TimeRange:
    starts_at: datetime
    ends_at: datetime

    def __post_init__(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("end must be after start")

    @property
    def duration(self) -> timedelta:
        return self.ends_at - self.starts_at

    def overlaps(self, other: "TimeRange") -> bool:
        return self.starts_at < other.ends_at and other.starts_at < self.ends_at

@dataclass(frozen=True, slots=True)
class BookingRequest:
    seat_id: SeatId
    user_id: UserId
    period: TimeRange

@dataclass(frozen=True, slots=True)
class Booking:
    id: BookingId
    seat_id: SeatId
    user_id: UserId
    period: TimeRange