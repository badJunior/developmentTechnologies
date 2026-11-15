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
