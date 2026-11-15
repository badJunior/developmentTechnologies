from booking.domain.models import Booking, SeatId, TimeRange

class InMemoryBookingRepository:
    def __init__(self) -> None:
        self._bookings: list[Booking] = []

    async def add(self, booking: Booking) -> None:
        self._bookings.append(booking)

    async def find_overlapping(self, seat_id: SeatId, period: TimeRange) -> list[Booking]:
        return [b for b in self._bookings if b.seat_id == seat_id and b.period.overlaps(period)]
