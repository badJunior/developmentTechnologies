from booking.adapters.in_memory_repository import InMemoryBookingRepository
from booking.adapters.logging_notifier import LoggingNotifier
from booking.adapters.system_clock import SystemClock, UuidIdGenerator
from booking.services.booking_service import BookingService
from booking.services.policies import policy_for

_repo = InMemoryBookingRepository()

async def get_booking_service() -> BookingService:
    return BookingService(_repo, SystemClock(), UuidIdGenerator(), LoggingNotifier(), policy_for)
