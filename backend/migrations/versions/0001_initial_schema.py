"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-06-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("passport_number", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_candidates_email", "candidates", ["email"], unique=True)
    op.create_index("ix_candidates_passport_number", "candidates", ["passport_number"], unique=True)

    op.create_table(
        "test_slots",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("test_center_name", sa.String(length=255), nullable=False),
        sa.Column("test_type", sa.String(length=20), nullable=False),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("test_time", sa.Time(), nullable=False),
        sa.Column("available_seats", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("available_seats >= 0", name="ck_test_slots_available_seats_non_negative"),
        sa.CheckConstraint("test_type IN ('Academic', 'General')", name="ck_test_slots_test_type_valid"),
    )
    op.create_index("ix_test_slots_city", "test_slots", ["city"], unique=False)
    op.create_index("ix_test_slots_test_date", "test_slots", ["test_date"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("booking_reference", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("slot_id", sa.Integer(), nullable=False),
        sa.Column("booking_status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("payment_status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("booking_status IN ('pending', 'confirmed', 'cancelled')", name="ck_bookings_booking_status_valid"),
        sa.CheckConstraint("payment_status IN ('pending', 'paid', 'failed', 'refunded')", name="ck_bookings_payment_status_valid"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_id"], ["test_slots.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_bookings_booking_reference", "bookings", ["booking_reference"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_bookings_booking_reference", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_test_slots_test_date", table_name="test_slots")
    op.drop_index("ix_test_slots_city", table_name="test_slots")
    op.drop_table("test_slots")
    op.drop_index("ix_candidates_passport_number", table_name="candidates")
    op.drop_index("ix_candidates_email", table_name="candidates")
    op.drop_table("candidates")

