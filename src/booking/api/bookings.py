from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from booking.api.security import CurrentUser, require_user
from booking.domain.models import BookingRequest, SeatId, TimeRange
from booking.services.booking_service import BookingService
from booking.api.dependencies import get_booking_service

router = APIRouter(prefix="/v1", tags=["bookings"])

class CreateBookingRequest(BaseModel):
    seat_id: UUID
    starts_at: datetime
    ends_at: datetime

@router.post("/bookings", status_code=201)
async def create_booking(
    payload: CreateBookingRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    service: Annotated[BookingService, Depends(get_booking_service)],
):
    try:
        req = BookingRequest(SeatId(str(payload.seat_id)), user.id, TimeRange(payload.starts_at, payload.ends_at))
        booking = await service.create(req)
        return {"id": booking.id}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/seats")
async def list_seats():
    return [{"id": "11111111-1111-1111-1111-111111111111", "code": "desk-1"}]
