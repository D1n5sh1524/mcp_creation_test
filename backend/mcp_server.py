from __future__ import annotations

from datetime import date

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Booking, Candidate, TestSlot
from app.schemas import BookingCreate, CandidateCreate

mcp = FastMCP("ielts-booking")


def _slot_to_dict(slot: TestSlot) -> dict:
    return {
        "id": slot.id,
        "city": slot.city,
        "test_center_name": slot.test_center_name,
        "test_type": slot.test_type,
        "test_date": slot.test_date.isoformat(),
        "test_time": slot.test_time.isoformat(),
        "available_seats": slot.available_seats,
        "created_at": slot.created_at.isoformat(),
        "updated_at": slot.updated_at.isoformat(),
    }


def _booking_to_dict(booking: Booking) -> dict:
    return {
        "id": booking.id,
        "booking_reference": str(booking.booking_reference),
        "candidate_id": booking.candidate_id,
        "slot_id": booking.slot_id,
        "booking_status": booking.booking_status,
        "payment_status": booking.payment_status,
        "created_at": booking.created_at.isoformat(),
        "updated_at": booking.updated_at.isoformat(),
    }


@mcp.tool()
def list_test_slots(city: str | None = None, test_date: str | None = None) -> list[dict]:
    """List available IELTS test slots, optionally filtered by city or test date."""
    parsed_date = date.fromisoformat(test_date) if test_date else None
    statement = select(TestSlot).order_by(TestSlot.test_date, TestSlot.test_time, TestSlot.city)
    if city:
        statement = statement.where(TestSlot.city == city)
    if parsed_date:
        statement = statement.where(TestSlot.test_date == parsed_date)

    with SessionLocal() as db:
        return [_slot_to_dict(slot) for slot in db.scalars(statement).all()]


@mcp.tool()
def get_test_slot(slot_id: int) -> dict:
    """Get a single IELTS test slot by ID."""
    with SessionLocal() as db:
        slot = db.get(TestSlot, slot_id)
        if slot is None:
            raise ValueError("Test slot not found")
        return _slot_to_dict(slot)


@mcp.tool()
def book_test_slot(slot_id: int, candidate: dict) -> dict:
    """Create a booking for a slot. Creates the candidate if they do not already exist."""
    try:
        candidate_payload = CandidateCreate.model_validate(candidate)
        payload = BookingCreate(slot_id=slot_id, candidate=candidate_payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid booking payload: {exc}") from exc

    with SessionLocal() as db:
        slot = db.get(TestSlot, payload.slot_id)
        if slot is None:
            raise ValueError("Test slot not found")
        if slot.available_seats <= 0:
            raise ValueError("No seats available for this slot")

        existing_candidate = db.scalar(select(Candidate).where(Candidate.email == payload.candidate.email))
        candidate_created = False
        if existing_candidate is None:
            existing_candidate = Candidate(**payload.candidate.model_dump())
            db.add(existing_candidate)
            db.flush()
            candidate_created = True

        booking = Booking(candidate_id=existing_candidate.id, slot_id=slot.id)
        db.add(booking)
        slot.available_seats -= 1
        db.commit()
        db.refresh(booking)

        return {
            "booking": _booking_to_dict(booking),
            "candidate_created": candidate_created,
            "slot_remaining_seats": slot.available_seats,
        }


if __name__ == "__main__":
    mcp.run()
