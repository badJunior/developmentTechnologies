import os
from pathlib import Path


def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан: {path}")


# --- 1. Каталоги для тестов ---
Path("tests/unit").mkdir(parents=True, exist_ok=True)
Path("tests/integration").mkdir(parents=True, exist_ok=True)
Path("tests/contract").mkdir(parents=True, exist_ok=True)
Path("tests/e2e").mkdir(parents=True, exist_ok=True)
Path("tests/load").mkdir(parents=True, exist_ok=True)

# --- 2. Тест на границы интервалов (AC-04.3) ---
test_boundaries = """
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
    \"\"\"Проверяем правило полуоткрытого интервала [start, end).\"\"\"
    base_range = TimeRange(BASE.replace(hour=9), BASE.replace(hour=12))
    test_range = TimeRange(BASE.replace(hour=start_hour), BASE.replace(hour=end_hour))

    assert base_range.overlaps(test_range) == expected
"""
create_file("tests/unit/test_time_range_boundaries.py", test_boundaries)

# --- 3. Тест на пределы длительности ---
test_duration = """
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
    \"\"\"Проверяем границы: 30 минут и 8 часов.\"\"\"
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
"""
create_file("tests/unit/test_duration_bounds.py", test_duration)

# --- 4. Тестовая нагрузка (k6) ---
k6_test = """
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    nfr01: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 20,
      maxVUs: 50,
    },
  },
  thresholds: {
    'http_req_duration{expected_response:true}': ['p(95)<300'],
    'http_req_failed': ['rate<0.01'],
  },
};

const today = new Date().toISOString().slice(0, 10);

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/health`);
  check(res, { 'status is 200': (r) => r.status === 200 });
}
"""
create_file("tests/load/smoke.js", k6_test)

# --- 5. Документация по стратегии тестирования ---
strategy = """
# Стратегия тестирования

## Уровни

| Уровень | Что проверяет | Где лежит | Тестов |
|---|---|---|---|
| Модульные | Правила, интервалы, границы | tests/unit/ | 150+ |
| Интеграционные | База данных, API | tests/integration/ | 50+ |
| Контрактные | Соответствие OpenAPI | tests/contract/ | 10+ |
| Сквозные | Сборка частей | tests/e2e/ | 3-5 |

**Правило:** Новый тест на правило → модульный. На работу с базой → интеграционный.

## Техники

- **Классы эквивалентности:** длительность (0, 30 мин, 3 ч, 8 ч, 10 ч).
- **Граничные значения:** 29/30/31 мин, 7:59/8:00/8:01.
- **Таблица решений:** отмена брони (роль × владелец × причина × состояние).

## Пороги качества

| Порог | Значение | Почему |
|---|---|---|
| Покрытие по ветвям | ≥ 70 % | Ниже — код не проверен |
| Все тесты зелёные | — | — |
| Линтер и типы | — | — |
| Время прогона | ≤ 60 с | NFR-05 |
| Уязвимости зависимостей | Нет высоких | `pip-audit` |
| Секреты | Нет | `gitleaks` |

## Что не проверяем

- Нагрузка до насыщения (нужен стенд).
- Локализация (один язык).
- Безопасность сканером (вне курса).
"""
create_file("docs/testing/strategy.md", strategy)

print("\\n✅ Все файлы для ЛР 5 созданы!")
print("Теперь выполните в терминале:")
print("uv add --dev pytest-randomly pytest-repeat pytest-xdist mutmut")