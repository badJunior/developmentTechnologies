from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

def register_error_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, error: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Validation failed"})
