import os
from pathlib import Path


def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан: {path}")


# 1. Сервис бронирования
booking_service = """
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

from booking.domain import rules
from booking.domain.errors import SeatAlreadyBooked
from booking.domain.models import Booking, BookingRequest, SeatId, TimeRange, UserId
from booking.domain.rules import WorkingHours

@dataclass
class BookingPolicy:
    working_hours: WorkingHours
    max_duration: timedelta

class BookingService:
    def __init__(self, repository, clock, ids, notifier, policy_for):
        self._repository = repository
        self._clock = clock
        self._ids = ids
        self._notifier = notifier
        self._policy_for = policy_for

    async def create(self, request: BookingRequest) -> Booking:
        kind = "desk" if not str(request.seat_id).startswith("room") else "meeting_room"
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
        self._notifier.booking_created(booking.user_id, booking.id)

        structlog.get_logger().info("booking_created", booking_id=booking.id)
        return booking
"""
create_file("src/booking/services/booking_service.py", booking_service)

# 2. Политики для видов мест
policies = """
from datetime import time, timedelta
from booking.domain.rules import WorkingHours
from booking.services.booking_service import BookingPolicy

DESK_POLICY = BookingPolicy(WorkingHours(), timedelta(hours=8))
ROOM_POLICY = BookingPolicy(WorkingHours(time(9), time(20)), timedelta(hours=3))

def policy_for(kind: str) -> BookingPolicy:
    return ROOM_POLICY if kind == "meeting_room" else DESK_POLICY
"""
create_file("src/booking/services/policies.py", policies)

# 3. Обработчики API
api_bookings = """
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from booking.api.security import CurrentUser, require_user
from booking.domain.models import BookingRequest, SeatId, TimeRange, UserId
from booking.services.booking_service import BookingService
from booking.services.factory import get_booking_service

router = APIRouter(prefix="/v1", tags=["bookings"])

class CreateBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seat_id: UUID
    starts_at: datetime
    ends_at: datetime

class BookingResponse(BaseModel):
    id: str
    seat_id: str
    user_id: str
    starts_at: datetime
    ends_at: datetime

@router.post("/bookings", status_code=201, response_model=BookingResponse)
async def create_booking(
    payload: CreateBookingRequest,
    response: Response,
    user: Annotated[CurrentUser, Depends(require_user)],
    service: Annotated[BookingService, Depends(get_booking_service)],
):
    try:
        req = BookingRequest(SeatId(str(payload.seat_id)), user.id, TimeRange(payload.starts_at, payload.ends_at))
        booking = await service.create(req)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    return BookingResponse(
        id=booking.id, seat_id=booking.seat_id, user_id=booking.user_id,
        starts_at=booking.period.starts_at, ends_at=booking.period.ends_at
    )

@router.get("/seats", response_model=list)
async def list_seats():
    return [{"id": "11111111-1111-1111-1111-111111111111", "code": "desk-1", "kind": "desk"}]
"""
create_file("src/booking/api/bookings.py", api_bookings)

# 4. Фабрика зависимостей (корень композиции)
deps = """
from fastapi import Depends, Request
from typing import Annotated
from booking.config import Settings, get_settings
from booking.adapters.in_memory_repository import InMemoryBookingRepository
from booking.adapters.logging_notifier import LoggingNotifier
from booking.adapters.system_clock import SystemClock, UuidIdGenerator
from booking.services.booking_service import BookingService
from booking.services.policies import policy_for

_repo = InMemoryBookingRepository()

async def get_booking_service(settings: Annotated[Settings, Depends(get_settings)]) -> BookingService:
    return BookingService(
        repository=_repo,
        clock=SystemClock(),
        ids=UuidIdGenerator(),
        notifier=LoggingNotifier(),
        policy_for=policy_for,
    )
"""
create_file("src/booking/api/dependencies.py", deps)

print("\n✅ Файлы эндпоинтов созданы!")