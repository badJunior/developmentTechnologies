import os
from pathlib import Path


def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан/обновлен: {path}")


# --- ЛР 6Б: Многоэтапный Dockerfile ---
dockerfile = """
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \\
    UV_LINK_MODE=copy \\
    UV_HTTP_TIMEOUT=120 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY README.md ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --gid 10001 appuser \\
    && useradd --uid 10001 --gid appuser --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --from=builder --chown=appuser:appuser /app/src /app/src

USER appuser
ARG APP_VERSION=0.0.0-dev
ENV APP_VERSION=$APP_VERSION
EXPOSE 8080
CMD ["python", "-m", "booking"]
"""
create_file("Dockerfile", dockerfile)

# --- ЛР 6Б: .dockerignore ---
dockerignore = """
.git
.github
.venv
__pycache__
*.py[cod]
.pytest_cache
.ruff_cache
.mypy_cache
.coverage
htmlcov
.env
docs
tests
seeds
*.md
!README.md
compose*.yaml
Dockerfile*
.trivyignore
"""
create_file(".dockerignore", dockerignore)

# --- ЛР 7: Метрики ---
metrics_py = """
from prometheus_client import CollectorRegistry, Counter, Histogram

REGISTRY = CollectorRegistry()

http_requests = Counter(
    "http_requests_total", "Requests served",
    labelnames=("method", "path", "status"), registry=REGISTRY,
)

http_duration = Histogram(
    "http_request_duration_seconds", "Request duration",
    labelnames=("method", "path", "outcome"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)
"""
create_file("src/booking/observability/metrics.py", metrics_py)

# --- ЛР 7: Проверка готовности ---
ready_py = """
from fastapi import APIRouter, Response
from typing import Literal
from pydantic import BaseModel

router = APIRouter(tags=["system"])

class ReadyResponse(BaseModel):
    status: Literal["ok", "degraded", "unavailable"]

@router.get("/ready", response_model=ReadyResponse)
async def ready(response: Response) -> ReadyResponse:
    # Заглушка для проверки работоспособности
    response.status_code = 200
    return ReadyResponse(status="ok")
"""
create_file("src/booking/api/ready.py", ready_py)

# --- ЛР 7: Обновление app.py ---
app_py = """
import structlog
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from booking.api import system, bookings, ready
from booking.api.middleware import request_context
from booking.api.errors import register_error_handlers
from booking.config import Settings, get_settings
from booking.logging import configure_logging

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.environment)

    app = FastAPI(title="Booking API", version=settings.app_version)
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_context)

    register_error_handlers(app)

    app.include_router(system.router)
    app.include_router(bookings.router)
    app.include_router(ready.router) # <-- Добавлен роутер готовности

    app.dependency_overrides.setdefault(get_settings, lambda: settings)

    structlog.get_logger().info("service_started", version=settings.app_version)
    return app
"""
create_file("src/booking/app.py", app_py)

print("\n✅ Файлы для ЛР 6Б и ЛР 7 созданы!")
print("Теперь выполните в терминале:")
print("docker compose down")
print("docker compose up -d --build")