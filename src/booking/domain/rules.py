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
