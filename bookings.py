from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from uuid import UUID

# --- Заменяем импорты на относительные ---
from .security import CurrentUser, require_user
from ..domain.models import BookingRequest, SeatId, TimeRange
from ..services.booking_service import BookingService
from .dependencies import get_booking_service

# -----------------------------------------

router = APIRouter(prefix="/v1", tags=["bookings"])


class CreateBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seat_id: UUID
    starts_at: datetime
    ends_at: datetime


class BookingResponse(BaseModel):
    id: str
    seat_id: str
    user_id: str
    starts_at: datetime
    ends_at: datetime


@router.post("/bookings", status_code=201, response_model=BookingResponse)
async def create_booking(
        payload: CreateBookingRequest,
        response: Response,
        user: Annotated[CurrentUser, Depends(require_user)],
        service: Annotated[BookingService, Depends(get_booking_service)],
):
    try:
        req = BookingRequest(SeatId(str(payload.seat_id)), user.id, TimeRange(payload.starts_at, payload.ends_at))
        booking = await service.create(req)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    return BookingResponse(
        id=booking.id, seat_id=booking.seat_id, user_id=booking.user_id,
        starts_at=booking.period.starts_at, ends_at=booking.period.ends_at
    )


@router.get("/seats", response_model=list)
async def list_seats():
    return [{"id": "11111111-1111-1111-1111-111111111111", "code": "desk-1", "kind": "desk"}]