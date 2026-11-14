import pytest
from datetime import datetime, timedelta, timezone
from booking.domain.models import BookingRequest, SeatId, TimeRange, UserId

UTC = timezone.utc
BASE = datetime(2030, 1, 1, 9, 0, tzinfo=UTC)

@pytest.mark.parametrize(
    ("hours", "should_fail"),
    [
        (7.5, False),   # меньше предела
        (8.0, False),   # ровно предел
        (8.1, True),    # больше предела
        (0.4, True),    # меньше минимума (30 мин)
        (0.5, False),   # ровно минимум
    ],
    ids=["below_limit", "at_limit", "above_limit", "below_min", "at_min"]
)
def test_duration_bounds(hours, should_fail):
    """Проверяем границы: 30 минут и 8 часов."""
    from booking.domain.rules import require_duration_at_most, require_valid_period
    from booking.domain.errors import BookingTooLong, InvalidPeriod

    req = BookingRequest(SeatId("desk-1"), UserId("u-1"), TimeRange(BASE, BASE + timedelta(hours=hours)))

    if should_fail:
        with pytest.raises((BookingTooLong, InvalidPeriod)):
            require_valid_period(req)
            require_duration_at_most(req, timedelta(hours=8))
    else:
        require_valid_period(req)
        require_duration_at_most(req, timedelta(hours=8))
