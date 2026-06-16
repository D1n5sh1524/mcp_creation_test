import uuid
from datetime import date, time
from datetime import datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Time, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TestSlot(TimestampMixin, Base):
    __tablename__ = "test_slots"
    __table_args__ = (
        Index("ix_test_slots_city", "city"),
        Index("ix_test_slots_test_date", "test_date"),
        CheckConstraint("available_seats >= 0", name="ck_test_slots_available_seats_non_negative"),
        CheckConstraint("test_type IN ('Academic', 'General')", name="ck_test_slots_test_type_valid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    test_center_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_type: Mapped[str] = mapped_column(String(20), nullable=False)
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    test_time: Mapped[time] = mapped_column(Time, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="slot", cascade="all, delete-orphan")


class Candidate(TimestampMixin, Base):
    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_candidates_email", "email", unique=True),
        Index("ix_candidates_passport_number", "passport_number", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    passport_number: Mapped[str] = mapped_column(String(50), nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_booking_reference", "booking_reference", unique=True),
        CheckConstraint("booking_status IN ('pending', 'confirmed', 'cancelled')", name="ck_bookings_booking_status_valid"),
        CheckConstraint("payment_status IN ('pending', 'paid', 'failed', 'refunded')", name="ck_bookings_payment_status_valid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_reference: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    slot_id: Mapped[int] = mapped_column(ForeignKey("test_slots.id", ondelete="RESTRICT"), nullable=False)
    booking_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))

    candidate: Mapped[Candidate] = relationship(back_populates="bookings")
    slot: Mapped[TestSlot] = relationship(back_populates="bookings")
