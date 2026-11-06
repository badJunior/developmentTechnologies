# План семестра

```mermaid
gantt
    title Проект «Бронирование переговорных комнат»
    dateFormat YYYY-MM-DD
    axisFormat %d.%m

    section Основание (ЛР 1)
    Требования, персоны и CJM :done, m1, 2026-10-15, 7d
    User Story Map и процесс :done, m2, after m1, 7d

    section Проектирование (ЛР 2)
    Уточнение требований и NFR :m3, after m2, 7d
    Модель предметной области :m4, after m3, 7d
    Архитектура и решения :m5, after m4, 7d
    Модели и ресурсы API :m6, after m5, 7d

    section Каркас (ЛР 3)
    Сервис и окружение :m7, after m6, 7d
    Логика в коде, тесты :m8, after m7, 7d

    section Реализация (ЛР 4-5)
    Данные и миграции :m9, after m8, 7d
    API и контракт :m10, after m9, 7d
    Тестирование и качество :m11, after m10, 7d

    section Зрелость и Защита (ЛР 6-9)
    Асинхронность и уведомления :m12, after m11, 14d
    Клиентское приложение :m13, after m12, 14d
    Аудит и документация :m14, after m13, 7d
    
    section Буфер
    Резерв времени :buf, after m14, 7d
    Защита проекта :milestone, defend, after buf, 0d
