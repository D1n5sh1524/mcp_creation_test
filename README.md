# IELTS Booking DB Scaffold

This repository contains a production-oriented local development setup for an IELTS booking backend.

## Stack

- PostgreSQL 16
- Docker Compose
- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- Alembic

## Layout

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

## Quick Start

```bash
docker compose up -d
cd backend
alembic upgrade head
```

## Alembic Commands

```bash
alembic revision --autogenerate -m "new change"
alembic downgrade -1
```

## MCP Server

The repo also includes an MCP server that exposes tools for:

- listing test slots
- reading a single slot by ID
- creating a booking for a slot

Run it with:

```bash
./.venv/bin/python backend/mcp_server.py
```

The tools are:

- `list_test_slots(city?, test_date?)`
- `get_test_slot(slot_id)`
- `book_test_slot(slot_id, candidate)`

If you are connecting Continue to this server, the active workspace config is:

```text
.continue/mcpServers/new-mcp-server-1.yaml
```

For connection and usage details, see [HOW_IT_WORKS.md](./HOW_IT_WORKS.md).

For a plain-English walkthrough of the repo, see [HOW_IT_WORKS.md](./HOW_IT_WORKS.md).

## Notes

- PostgreSQL runs on port `5432`.
- Default database is `ielts_booking`.
- Default user is `ielts`.
- Default password is `ielts123`.
- Booking references are generated as UUIDs.
- local db host :http://localhost:5050
