import pytest
from datetime import datetime, timedelta, timezone
from booking.domain.models import TimeRange

UTC = timezone.utc
BASE = datetime(2030, 1, 1, 9, 0, tzinfo=UTC)

@pytest.mark.parametrize(
    ("start_hour", "end_hour", "expected"),
    [
        (9, 12, True),    # полное совпадение
        (10, 11, True),   # внутри
        (8, 10, True),    # пересекает начало
        (11, 13, True),   # пересекает конец
        (8, 13, True),    # покрывает
        (7, 9, False),    # соприкасается до (граница AC-04.3)
        (12, 14, False),  # соприкасается после (граница AC-04.3)
        (14, 16, False),  # далеко
    ],
    ids=["same", "inside", "overlaps_start", "overlaps_end", "covers", "touches_before", "touches_after", "apart"]
)
def test_time_range_overlaps(start_hour, end_hour, expected):
    """Проверяем правило полуоткрытого интервала [start, end)."""
    base_range = TimeRange(BASE.replace(hour=9), BASE.replace(hour=12))
    test_range = TimeRange(BASE.replace(hour=start_hour), BASE.replace(hour=end_hour))

    assert base_range.overlaps(test_range) == expected
