import os
from pathlib import Path


def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан: {path}")


# 1. pyproject.toml
pyproject = """
[project]
name = "booking"
version = "0.1.0"
description = "Meeting room booking service"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic-settings>=2.6.0",
    "structlog>=24.4.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.3.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.27.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.13"
disallow_untyped_defs = true
warn_unused_ignores = true
warn_return_any = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"
pythonpath = ["."]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
create_file("pyproject.toml", pyproject)

# 2. .env.example
env_example = """
# Порт, на котором сервис принимает запросы
PORT=8080

# Уровень журнала: debug | info | warning | error
LOG_LEVEL=info

# Среда запуска: development | test | production
ENVIRONMENT=development

# Адрес базы данных. ОБЯЗАТЕЛЬНАЯ переменная.
DATABASE_URL=postgresql://booking:booking@db:5432/booking
"""
create_file(".env.example", env_example)

# 3. Настройки (config.py)
config_py = """
from functools import lru_cache
from typing import Literal
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["debug", "info", "warning", "error"]
Environment = Literal["development", "test", "production"]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    port: int = Field(default=8080, ge=1, le=65535)
    log_level: LogLevel = "info"
    environment: Environment = "development"
    app_version: str = "0.0.0-dev"
    database_url: PostgresDsn

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
"""
create_file("src/booking/config.py", config_py)

# 4. Журнал (logging.py)
logging_py = """
import logging
import sys
import structlog
from booking.config import Environment, LogLevel

_LEVELS: dict[LogLevel, int] = {
    "debug": logging.DEBUG, "info": logging.INFO,
    "warning": logging.WARNING, "error": logging.ERROR,
}

def configure_logging(level: LogLevel, environment: Environment) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=_LEVELS[level])

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if environment == "development":
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(_LEVELS[level]),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )
"""
create_file("src/booking/logging.py", logging_py)

# 5. Middleware
middleware_py = """
import time
import uuid
from collections.abc import Awaitable, Callable
import structlog
from fastapi import Request, Response

REQUEST_ID_HEADER = "X-Request-Id"

async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    request.state.request_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)

    logger = structlog.get_logger()
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", duration_ms=int((time.perf_counter() - started) * 1000))
        raise
    logger.info("request_handled", status_code=response.status_code, duration_ms=int((time.perf_counter() - started) * 1000))
    response.headers[REQUEST_ID_HEADER] = request_id
    return response
"""
create_file("src/booking/api/middleware.py", middleware_py)

# 6. Обработчики /health и /version
system_py = """
from typing import Annotated, Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from booking.config import Settings, get_settings

router = APIRouter(tags=["system"])

class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"

class VersionResponse(BaseModel):
    version: str = Field(examples=["1.2.3"])
    environment: str = Field(examples=["production"])

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()

@router.get("/version", response_model=VersionResponse)
async def version(settings: Annotated[Settings, Depends(get_settings)]) -> VersionResponse:
    return VersionResponse(version=settings.app_version, environment=settings.environment)
"""
create_file("src/booking/api/system.py", system_py)

# 7. Фабрика приложения (app.py)
app_py = """
import structlog
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from booking.api import system
from booking.api.middleware import request_context
from booking.config import Settings, get_settings
from booking.logging import configure_logging

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.environment)

    app = FastAPI(title="Booking API", version=settings.app_version)
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_context)
    app.include_router(system.router)
    app.dependency_overrides.setdefault(get_settings, lambda: settings)

    structlog.get_logger().info("service_started", version=settings.app_version)
    return app
"""
create_file("src/booking/app.py", app_py)

# 8. Точка входа (__main__.py)
main_py = """
import uvicorn
from booking.config import get_settings

def main() -> None:
    settings = get_settings()
    uvicorn.run("booking.app:create_app", factory=True, host="0.0.0.0", port=settings.port, log_config=None)

if __name__ == "__main__":
    main()
"""
create_file("src/booking/__main__.py", main_py)

# 9. Тесты (conftest.py)
conftest_py = """
from collections.abc import Iterator
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from booking.app import create_app
from booking.config import Settings

TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/test"

@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", log_level="warning", app_version="0.0.0-test", database_url=TEST_DATABASE_URL)

@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings=settings)) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.chdir(tmp_path)
"""
create_file("tests/conftest.py", conftest_py)

# 10. Тесты обработчиков
test_api_py = """
from fastapi.testclient import TestClient
from booking.api.middleware import REQUEST_ID_HEADER

def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_version_reports_configured_version(client: TestClient) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "0.0.0-test", "environment": "test"}

def test_request_id_is_returned(client: TestClient) -> None:
    assert client.get("/health").headers[REQUEST_ID_HEADER]
"""
create_file("tests/test_system_api.py", test_api_py)

print("\nВсе файлы сервиса успешно созданы!")
print("Теперь выполните в терминале: uv sync && uv run pytest")