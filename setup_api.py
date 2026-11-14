import os
from pathlib import Path


def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан: {path}")


# 1. Хеширование паролей
passwords_py = """
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash("never-matches-any-password")

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(stored_hash: str | None, password: str) -> bool:
    try:
        _hasher.verify(stored_hash or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return stored_hash is not None
"""
create_file("src/booking/services/passwords.py", passwords_py)

# 2. Обработка ошибок (единый формат)
errors_py = """
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

PROBLEM_BASE = "https://api.booking.example/problems"
MEDIA_TYPE = "application/problem+json"

def problem(request: Request, status: int, slug: str, title: str, detail: str | None = None):
    body = {
        "type": f"{PROBLEM_BASE}/{slug}",
        "title": title,
        "status": status,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", ""),
    }
    if detail:
        body["detail"] = detail
    return JSONResponse(status_code=status, content=body, media_type=MEDIA_TYPE)

def register_error_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, error: RequestValidationError):
        return problem(request, 422, "validation-failed", "Данные не прошли проверку")

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, error: Exception):
        structlog.get_logger().exception("unhandled_error", path=request.url.path)
        return problem(request, 500, "internal-error", "Внутренняя ошибка", "Обратитесь в поддержку, указав request_id")
"""
create_file("src/booking/api/errors.py", errors_py)

# 3. Проверка токена (Security)
security_py = """
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from booking.config import Settings, get_settings
from booking.domain.models import UserId

_bearer = HTTPBearer(auto_error=False)

class CurrentUser:
    def __init__(self, id: UserId, role: str):
        self.id = id
        self.role = role

async def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="No token provided")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret.get_secret_value(), algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return CurrentUser(id=UserId(payload["sub"]), role=payload["role"])
"""
create_file("src/booking/api/security.py", security_py)

# 4. Хранилище на PostgreSQL (Repository)
postgres_repo_py = """
from collections import defaultdict
import asyncpg
from booking.domain.errors import SeatAlreadyBooked
from booking.domain.models import (
    Booking, BookingId, BookingStatus, SeatId, TimeRange, UserId,
)

_INSERT = \"\"\"
    INSERT INTO bookings (id, seat_id, user_id, starts_at, ends_at, status)
    VALUES ($1, $2, $3, $4, $5, $6)
\"\"\"
_FIND_OVERLAPPING = \"\"\"
    SELECT id, seat_id, user_id, starts_at, ends_at, status
      FROM bookings
     WHERE seat_id = $1 AND status = 'active'
       AND tstzrange(starts_at, ends_at, '[)') && tstzrange($2, $3, '[)')
\"\"\"
_FIND_BY_ID = \"\"\"SELECT id, seat_id, user_id, starts_at, ends_at, status FROM bookings WHERE id = $1\"\"\"

class PostgresBookingRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def add(self, booking: Booking) -> None:
        try:
            await self._connection.execute(
                _INSERT, booking.id, booking.seat_id, booking.user_id,
                booking.period.starts_at, booking.period.ends_at, booking.status.value,
            )
        except asyncpg.exceptions.ExclusionViolationError as error:
            raise SeatAlreadyBooked(f"seat {booking.seat_id} is taken") from error

    async def find_overlapping(self, seat_id: SeatId, period: TimeRange) -> list[Booking]:
        rows = await self._connection.fetch(_FIND_OVERLAPPING, seat_id, period.starts_at, period.ends_at)
        return [_to_booking(row) for row in rows]

    async def find_by_id(self, booking_id: BookingId) -> Booking | None:
        row = await self._connection.fetchrow(_FIND_BY_ID, booking_id)
        return _to_booking(row) if row else None

def _to_booking(row: asyncpg.Record) -> Booking:
    return Booking(
        id=BookingId(str(row["id"])),
        seat_id=SeatId(str(row["seat_id"])),
        user_id=UserId(str(row["user_id"])),
        period=TimeRange(row["starts_at"], row["ends_at"]),
        status=BookingStatus(row["status"]),
    )
"""
create_file("src/booking/adapters/postgres_booking_repository.py", postgres_repo_py)

print("\n✅ Все файлы API и хранилища созданы успешно!")
print("Теперь выполните в терминале:")
print("uv add pyjwt argon2-cffi")