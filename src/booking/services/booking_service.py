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
