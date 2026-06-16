"""seed test slots

Revision ID: 0002_seed_test_slots
Revises: 0001_initial_schema
Create Date: 2026-06-16 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_seed_test_slots"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

test_slots = sa.table(
    "test_slots",
    sa.column("city", sa.String()),
    sa.column("test_center_name", sa.String()),
    sa.column("test_type", sa.String()),
    sa.column("test_date", sa.Date()),
    sa.column("test_time", sa.Time()),
    sa.column("available_seats", sa.Integer()),
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO test_slots
                (city, test_center_name, test_type, test_date, test_time, available_seats, created_at, updated_at)
            VALUES
                ('Chennai', 'IDP Chennai Anna Salai', 'Academic', DATE '2026-07-20', TIME '09:00:00', 15, now(), now()),
                ('Chennai', 'IDP Chennai Anna Salai', 'General', DATE '2026-07-20', TIME '14:00:00', 8, now(), now()),
                ('Bangalore', 'IDP Bangalore MG Road', 'Academic', DATE '2026-07-20', TIME '09:00:00', 12, now(), now())
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM test_slots
            WHERE city IN ('Chennai', 'Bangalore')
              AND test_center_name IN ('IDP Chennai Anna Salai', 'IDP Bangalore MG Road')
              AND test_date = DATE '2026-07-20'
            """
        )
    )
