from datetime import time, timedelta
from booking.domain.rules import WorkingHours
from booking.services.booking_service import BookingPolicy

DESK_POLICY = BookingPolicy(WorkingHours(), timedelta(hours=8))
ROOM_POLICY = BookingPolicy(WorkingHours(time(9), time(20)), timedelta(hours=3))

def policy_for(kind) -> BookingPolicy:
    return ROOM_POLICY if kind == "meeting_room" else DESK_POLICY
