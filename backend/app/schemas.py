from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel


class TestSlotRead(BaseModel):
    id: int
    city: str
    test_center_name: str
    test_type: str
    test_date: date
    test_time: time
    available_seats: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookingRead(BaseModel):
    id: int
    booking_reference: UUID
    candidate_id: int
    slot_id: int
    booking_status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    passport_number: str


class BookingCreate(BaseModel):
    slot_id: int
    candidate: CandidateCreate


class BookingCreateResponse(BaseModel):
    booking: BookingRead
    candidate_created: bool
    slot_remaining_seats: int

    model_config = {"from_attributes": True}
