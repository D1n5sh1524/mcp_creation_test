from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.chat import handle_booking_chat
from app.db.database import get_db
from app.db.models import Booking, Candidate, TestSlot
from app.schemas import BookingCreate, BookingCreateResponse, ChatRequest, ChatResponse, TestSlotRead

app = FastAPI(title="IELTS Booking API", version="0.1.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/test-slots", response_model=list[TestSlotRead])
def list_test_slots(
    city: str | None = Query(default=None, description="Filter by city"),
    test_date: date | None = Query(default=None, description="Filter by test date"),
    db: Session = Depends(get_db),
) -> list[TestSlot]:
    statement: Select[TestSlot] = select(TestSlot).order_by(TestSlot.test_date, TestSlot.test_time, TestSlot.city)

    if city:
        statement = statement.where(TestSlot.city == city)
    if test_date:
        statement = statement.where(TestSlot.test_date == test_date)

    return list(db.scalars(statement).all())


@app.get("/test-slots/{slot_id}", response_model=TestSlotRead)
def get_test_slot(slot_id: int, db: Session = Depends(get_db)) -> TestSlot:
    slot = db.get(TestSlot, slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="Test slot not found")
    return slot


@app.post("/bookings", response_model=BookingCreateResponse, status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)) -> BookingCreateResponse:
    slot = db.get(TestSlot, payload.slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="Test slot not found")
    if slot.available_seats <= 0:
        raise HTTPException(status_code=409, detail="No seats available for this slot")

    candidate = db.scalar(select(Candidate).where(Candidate.email == payload.candidate.email))
    candidate_created = False
    if candidate is None:
        candidate = Candidate(**payload.candidate.model_dump())
        db.add(candidate)
        db.flush()
        candidate_created = True

    booking = Booking(candidate_id=candidate.id, slot_id=slot.id)
    db.add(booking)
    slot.available_seats -= 1
    db.commit()
    db.refresh(booking)
    db.refresh(slot)

    return BookingCreateResponse(
        booking=booking,
        candidate_created=candidate_created,
        slot_remaining_seats=slot.available_seats,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> dict:
    return handle_booking_chat(
        message=payload.message,
        session=payload.session,
        selected_slot_id=payload.selected_slot_id,
    )
