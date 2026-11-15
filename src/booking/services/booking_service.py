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
