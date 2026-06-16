You are a senior backend engineer.

Create a production-quality PostgreSQL local development setup for an IELTS booking application.

Requirements:

## Tech Stack

- PostgreSQL 16
- Docker Compose
- Alembic migrations
- SQLAlchemy 2.0
- Python 3.12
- FastAPI

## Deliverables

Generate all files with complete code and folder structure.

### Folder Structure

```text
project/
├── docker-compose.yml
├── .env
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── __init__.py
│   │   ├── main.py
│   │   └── __init__.py
│   ├── alembic.ini
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── requirements.txt
│   └── Dockerfile
└── README.md
```

## Docker Requirements

Create a docker-compose.yml that:

- Starts PostgreSQL 16
- Creates database named `ielts_booking`
- Creates user `ielts`
- Uses password `ielts123`
- Exposes port 5432
- Uses persistent volume storage
- Includes health checks

## Database Schema

Create SQLAlchemy models and Alembic migration files for:

### test_slots

Fields:

- id (primary key)
- city
- test_center_name
- test_type (Academic / General)
- test_date
- test_time
- available_seats
- created_at
- updated_at

### candidates

Fields:

- id (primary key)
- first_name
- last_name
- email
- phone
- passport_number
- created_at
- updated_at

### bookings

Fields:

- id (primary key)
- booking_reference
- candidate_id (foreign key)
- slot_id (foreign key)
- booking_status
- payment_status
- created_at
- updated_at

## Alembic Requirements

Generate:

- alembic.ini
- migrations/env.py
- initial migration file

Migration must:

- create all tables
- create foreign keys
- create indexes
- support downgrade()

## Seed Data

Create a migration or seed script that inserts:

Test Slots:

1.
- Chennai
- IDP Chennai Anna Salai
- Academic
- 2026-07-20
- 09:00
- 15 seats

2.
- Chennai
- IDP Chennai Anna Salai
- General
- 2026-07-20
- 14:00
- 8 seats

3.
- Bangalore
- IDP Bangalore MG Road
- Academic
- 2026-07-20
- 09:00
- 12 seats

## README

Include commands for:

```bash
docker compose up -d

alembic upgrade head

alembic revision --autogenerate -m "new change"

alembic downgrade -1
```

## Quality Requirements

- Use SQLAlchemy 2.0 style
- Use timezone-aware timestamps
- Use UUID booking references
- Add proper constraints
- Add indexes on city, test_date, booking_reference
- Follow production best practices
- Return complete code for every file
- Do not use placeholders or pseudo-code