import os
from pathlib import Path

def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан: {path}")

# --- 1. ПАПКА domain (если её нет) ---
domain_models = """
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
"""
create_file("src/booking/domain/models.py", domain_models)

domain_rules = """
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from booking.domain.errors import BookingTooLong, InvalidPeriod, OutsideWorkingHours
from booking.domain.models import BookingRequest

@dataclass(frozen=True)
class WorkingHours:
    opens_at: time = time(8, 0)
    closes_at: time = time(22, 0)

    def contains(self, moment: datetime) -> bool:
        return self.opens_at <= moment.timetz().replace(tzinfo=None) <= self.closes_at

def require_valid_period(request: BookingRequest) -> None:
    if request.period.duration < timedelta(minutes=30):
        raise InvalidPeriod("booking is shorter than the minimum slot")

def require_within_working_hours(request: BookingRequest, hours: WorkingHours) -> None:
    if not hours.contains(request.period.starts_at) or not hours.contains(request.period.ends_at):
        raise OutsideWorkingHours("outside working hours")

def require_duration_at_most(request: BookingRequest, limit: timedelta) -> None:
    if request.period.duration > limit:
        raise BookingTooLong(f"duration exceeds {limit}")

def require_not_in_past(request: BookingRequest, now: datetime) -> None:
    if request.period.starts_at < now:
        raise InvalidPeriod("booking starts in the past")
"""
create_file("src/booking/domain/rules.py", domain_rules)

domain_errors = """
class DomainError(Exception): pass
class InvalidPeriod(DomainError): pass
class OutsideWorkingHours(DomainError): pass
class BookingTooLong(DomainError): pass
class SeatAlreadyBooked(DomainError): pass
"""
create_file("src/booking/domain/errors.py", domain_errors)
create_file("src/booking/domain/__init__.py", "")

# --- 2. ПАПКА ports ---
ports_repo = """
from typing import Protocol
from booking.domain.models import Booking, SeatId, TimeRange

class BookingRepository(Protocol):
    async def add(self, booking: Booking) -> None: ...
    async def find_overlapping(self, seat_id: SeatId, period: TimeRange) -> list[Booking]: ...
"""
create_file("src/booking/ports/repository.py", ports_repo)

ports_clock = """
from datetime import datetime
from typing import Protocol
from booking.domain.models import BookingId

class Clock(Protocol):
    def now(self) -> datetime: ...

class IdGenerator(Protocol):
    def next_id(self) -> BookingId: ...
"""
create_file("src/booking/ports/clock.py", ports_clock)

ports_notifier = """
from typing import Protocol
from booking.domain.models import BookingId, UserId

class Notifier(Protocol):
    def booking_created(self, user_id: UserId, booking_id: BookingId) -> None: ...
"""
create_file("src/booking/ports/notifier.py", ports_notifier)
create_file("src/booking/ports/__init__.py", "")

# --- 3. ПАПКА adapters ---
in_mem = """
from booking.domain.models import Booking, SeatId, TimeRange

class InMemoryBookingRepository:
    def __init__(self) -> None:
        self._bookings: list[Booking] = []

    async def add(self, booking: Booking) -> None:
        self._bookings.append(booking)

    async def find_overlapping(self, seat_id: SeatId, period: TimeRange) -> list[Booking]:
        return [b for b in self._bookings if b.seat_id == seat_id and b.period.overlaps(period)]
"""
create_file("src/booking/adapters/in_memory_repository.py", in_mem)

sys_clock = """
from datetime import UTC, datetime
from uuid import uuid4
from booking.domain.models import BookingId

class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

class UuidIdGenerator:
    def next_id(self) -> BookingId:
        return BookingId(str(uuid4()))
"""
create_file("src/booking/adapters/system_clock.py", sys_clock)

log_notif = """
import structlog
from booking.domain.models import BookingId, UserId

class LoggingNotifier:
    def booking_created(self, user_id: UserId, booking_id: BookingId) -> None:
        structlog.get_logger().info("booking_created_notified", user_id=user_id, booking_id=booking_id)
"""
create_file("src/booking/adapters/logging_notifier.py", log_notif)
create_file("src/booking/adapters/__init__.py", "")

# --- 4. ПАПКА services ---
booking_svc = """
from dataclasses import dataclass
from datetime import timedelta
from booking.domain import rules
from booking.domain.errors import SeatAlreadyBooked
from booking.domain.models import Booking, BookingRequest
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

        booking = Booking(id=self._ids.next_id(), seat_id=request.seat_id, user_id=request.user_id, period=request.period)
        await self._repository.add(booking)
        self._notifier.booking_created(booking.user_id, booking.id)
        return booking
"""
create_file("src/booking/services/booking_service.py", booking_svc)

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

passwords = """
def hash_password(password: str) -> str:
    return password  # ВРЕМЕННО

def verify_password(stored_hash: str | None, password: str) -> bool:
    return True  # ВРЕМЕННО
"""
create_file("src/booking/services/passwords.py", passwords)
create_file("src/booking/services/__init__.py", "")

# --- 5. ПАПКА api ---
api_errors = """
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

def register_error_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, error: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Validation failed"})
"""
create_file("src/booking/api/errors.py", api_errors)

api_security = """
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from booking.domain.models import UserId

_bearer = HTTPBearer(auto_error=False)

class CurrentUser:
    def __init__(self, id: UserId, role: str):
        self.id = id
        self.role = role

async def require_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="No token")
    return CurrentUser(id=UserId("test-user"), role="visitor")
"""
create_file("src/booking/api/security.py", api_security)

api_deps = """
from booking.adapters.in_memory_repository import InMemoryBookingRepository
from booking.adapters.logging_notifier import LoggingNotifier
from booking.adapters.system_clock import SystemClock, UuidIdGenerator
from booking.services.booking_service import BookingService
from booking.services.policies import policy_for

_repo = InMemoryBookingRepository()

async def get_booking_service() -> BookingService:
    return BookingService(_repo, SystemClock(), UuidIdGenerator(), LoggingNotifier(), policy_for)
"""
create_file("src/booking/api/dependencies.py", api_deps)

api_bookings = """
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from booking.api.security import CurrentUser, require_user
from booking.domain.models import BookingRequest, SeatId, TimeRange
from booking.services.booking_service import BookingService
from booking.api.dependencies import get_booking_service

router = APIRouter(prefix="/v1", tags=["bookings"])

class CreateBookingRequest(BaseModel):
    seat_id: UUID
    starts_at: datetime
    ends_at: datetime

@router.post("/bookings", status_code=201)
async def create_booking(
    payload: CreateBookingRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    service: Annotated[BookingService, Depends(get_booking_service)],
):
    try:
        req = BookingRequest(SeatId(str(payload.seat_id)), user.id, TimeRange(payload.starts_at, payload.ends_at))
        booking = await service.create(req)
        return {"id": booking.id}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/seats")
async def list_seats():
    return [{"id": "11111111-1111-1111-1111-111111111111", "code": "desk-1"}]
"""
create_file("src/booking/api/bookings.py", api_bookings)

api_system = """
from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/health")
async def health():
    return {"status": "ok"}
"""
create_file("src/booking/api/system.py", api_system)
create_file("src/booking/api/__init__.py", "")

print("✅ ВСЁ ГОТОВО! Теперь запустите сервер: uv run python -m booking")