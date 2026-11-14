from collections import defaultdict
import asyncpg
from booking.domain.errors import SeatAlreadyBooked
from booking.domain.models import (
    Booking, BookingId, BookingStatus, SeatId, TimeRange, UserId,
)

_INSERT = """
    INSERT INTO bookings (id, seat_id, user_id, starts_at, ends_at, status)
    VALUES ($1, $2, $3, $4, $5, $6)
"""
_FIND_OVERLAPPING = """
    SELECT id, seat_id, user_id, starts_at, ends_at, status
      FROM bookings
     WHERE seat_id = $1 AND status = 'active'
       AND tstzrange(starts_at, ends_at, '[)') && tstzrange($2, $3, '[)')
"""
_FIND_BY_ID = """SELECT id, seat_id, user_id, starts_at, ends_at, status FROM bookings WHERE id = $1"""

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
