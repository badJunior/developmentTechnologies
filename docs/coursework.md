# Пояснительная записка к курсовой работе

**Дисциплина**: Технологии разработки программных систем
**Тема**: Бронирование переговорных комнат
**Команда**: Наумкин В., Мамонов Г., Чеснаков Р.

## 1. Введение
Проблема: сотрудники бизнес-центра не видят занятость комнат и сталкиваются.
Решение: сервис бронирования с календарём занятости.

## 2. Требования
См. `docs/requirements.md`.

## 3. Модель предметной области
См. `docs/domain/`.

## 4. Архитектурные решения
См. `docs/adr/`.

## 5. Контракт API
См. `docs/api/openapi.yaml`.

## 6. Модель данных
См. `migrations/`.

## 7. Испытания
См. `docs/testing/strategy.md`.

## 8. Развёртывание и эксплуатация
См. `docs/runbooks/`.

## 9. Системное проектирование
См. `docs/architecture-review.md`.

## 10. Прослеживаемость
См. `docs/traceability.md`.

## 11. Распределение работы
- Наумкин В.: серверная часть, база данных, API
- Мамонов Г.: клиентская часть, тесты, документация
- Чеснаков Р.: брокер, кеш, наблюдаемость

## 12. Долги и ограничения
См. `docs/CHANGELOG.md`.

## 13. Заключение
См. `docs/retrospective.md`.

## Приложение: артефакты
- ЛР 1: `docs/requirements.md`, `docs/process.md`
- ЛР 2: `docs/adr/`, `docs/domain/`, `docs/api/resources.md`
- ЛР 3: `Dockerfile`, `compose.yaml`
- ЛР 4: `migrations/`, `openapi.yaml`
- ЛР 5: `docs/testing/`
- ЛР 6: `docs/architecture/async-decisions.md`, `compose.prod.yaml`
- ЛР 7: `docs/slo.md`, `observability/`
- ЛР 8: `frontend/`
- ЛР 9: `docs/antipatterns/`, `docs/architecture-review.md`
