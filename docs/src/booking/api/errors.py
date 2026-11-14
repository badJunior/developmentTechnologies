from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

PROBLEM_BASE = "https://api.booking.example/problems"
MEDIA_TYPE = "application/problem+json"

def problem(request: Request, status: int, slug: str, title: str, detail: str | None = None):
    body = {
        "type": f"{PROBLEM_BASE}/{slug}",
        "title": title,
        "status": status,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", ""),
    }
    if detail:
        body["detail"] = detail
    return JSONResponse(status_code=status, content=body, media_type=MEDIA_TYPE)

def register_error_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, error: RequestValidationError):
        return problem(request, 422, "validation-failed", "Данные не прошли проверку")

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, error: Exception):
        structlog.get_logger().exception("unhandled_error", path=request.url.path)
        return problem(request, 500, "internal-error", "Внутренняя ошибка", "Обратитесь в поддержку, указав request_id")
