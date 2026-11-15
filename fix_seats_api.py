import re
from pathlib import Path

# Путь к файлу
file_path = Path("src/booking/api/bookings.py")

# Читаем текущий код
content = file_path.read_text(encoding="utf-8")

# Новый код для эндпоинта /seats
new_endpoint = '''
@router.get("/seats")
async def list_seats(date: str = "2026-12-01"):
    return [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "code": "desk-1",
            "kind": "desk",
            "capacity": 1,
            "is_available": True,
            "busy_intervals": []
        },
        {
            "id": "22222222-2222-2222-2222-222222222221",
            "code": "room-a",
            "kind": "meeting_room",
            "capacity": 8,
            "is_available": True,
            "busy_intervals": []
        }
    ]
'''

# Ищем старый эндпоинт (он может называться по-разному: /seats или /v1/seats)
# Регулярное выражение ищет декоратор @router.get(...) и функцию list_seats
pattern = r'@router\.get\(".*?/seats"\).*?async def list_seats.*?(?=\n@|\Z)'

# Заменяем
new_content = re.sub(pattern, new_endpoint, content, flags=re.DOTALL)

if new_content == content:
    print("❌ Не удалось найти эндпоинт /seats. Проверьте файл вручную.")
else:
    file_path.write_text(new_content, encoding="utf-8")
    print("✅ Эндпоинт /seats успешно обновлен!")

print("Теперь перезапустите сервер:")
print("uv run python -m booking")