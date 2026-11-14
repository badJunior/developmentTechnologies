import structlog
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from booking.api import system
from booking.api.middleware import request_context
from booking.api.errors import register_error_handlers  # <-- ДОБАВИТЬ ИМПОРТ
from booking.config import Settings, get_settings
from booking.logging import configure_logging
from booking.api import system, bookings

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.environment)

    app = FastAPI(title="Booking API", version=settings.app_version)
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_context)

    register_error_handlers(app)  # <-- ДОБАВИТЬ ВЫЗОВ

    app.include_router(system.router)
    app.include_router(bookings.router)
    app.dependency_overrides.setdefault(get_settings, lambda: settings)

    structlog.get_logger().info("service_started", version=settings.app_version)
    return app