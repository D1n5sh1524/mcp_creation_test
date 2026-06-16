# How This Repo Works

This repository is a local development scaffold for an IELTS booking system.
It gives you two ways to interact with the same PostgreSQL-backed data:

- a FastAPI HTTP app
- an MCP server for tool-based access from AI clients and editor integrations

## Big Picture

The data lives in PostgreSQL 16, which runs in Docker.
The Python code connects to that database with SQLAlchemy 2.0.
Alembic manages schema creation and seed data.

The repo is organized so the database schema, the API, and the MCP tools all point at the same tables.

## Main Pieces

### `docker-compose.yml`

This starts PostgreSQL 16 with:

- database name: `ielts_booking`
- user: `ielts`
- password: `ielts123`
- port: `5432`
- persistent volume storage
- a health check so Docker can tell when Postgres is ready

### `.env`

This stores local connection settings, especially `DATABASE_URL`.
Both the FastAPI app and Alembic use that connection string.

### `backend/app`

This is the FastAPI application layer.

- `main.py` defines the HTTP endpoints
- `db/database.py` creates the SQLAlchemy engine and session factory
- `db/models.py` defines the database tables
- `schemas.py` defines request and response models
- `settings.py` loads config from environment variables

### `backend/migrations`

This is the Alembic migration layer.

- `env.py` tells Alembic how to find the models and database URL
- `versions/0001_initial_schema.py` creates the tables and indexes
- `versions/0002_seed_test_slots.py` inserts the initial test slot rows

### `backend/mcp_server.py`

This is the MCP entrypoint.
It exposes the booking workflow as tools:

- list available test slots
- read one slot by ID
- book a slot for a candidate

## Data Model

There are three tables:

- `test_slots`
- `candidates`
- `bookings`

### `test_slots`

Stores available IELTS test sessions.
Important fields:

- `city`
- `test_center_name`
- `test_type`
- `test_date`
- `test_time`
- `available_seats`

Indexes exist on `city` and `test_date` for faster lookup.

### `candidates`

Stores the person booking the test.
Important fields:

- `first_name`
- `last_name`
- `email`
- `phone`
- `passport_number`

Email and passport number are indexed to keep candidate lookup fast and reduce duplicates.

### `bookings`

Stores the booking itself.
Important fields:

- `booking_reference`
- `candidate_id`
- `slot_id`
- `booking_status`
- `payment_status`

`booking_reference` is a UUID, so it is safe to expose externally.

## How The FastAPI App Works

The HTTP app is mainly for direct API access.

### `GET /health`

Simple health check for the app.

### `GET /test-slots`

Returns all seeded and newly created slots.
You can optionally filter by:

- `city`
- `test_date`

### `GET /test-slots/{slot_id}`

Returns one slot by its database ID.

### `POST /bookings`

Creates a booking for a slot.

What it does:

1. Checks that the slot exists
2. Checks that seats are still available
3. Reuses an existing candidate if the email already exists
4. Creates the booking
5. Decrements the slot seat count

## How The MCP Server Works

The MCP server exposes the same business capability in tool form.
It is meant for LLM clients, editors, and other MCP-compatible consumers.

Available tools:

- `list_test_slots(city?, test_date?)`
- `get_test_slot(slot_id)`
- `book_test_slot(slot_id, candidate)`

Behavior is intentionally close to the HTTP app:

- it queries the same database
- it uses the same models
- it creates bookings the same way

That means you can use either the HTTP API or the MCP server and get the same underlying result.

## How To Connect Continue To MCP

If you are using Continue in VS Code, point Continue at the MCP server with a YAML config.
In this repo, the working example is:

```yaml
mcpServers:
  - name: ielts-booking
    command: /Users/dineshkumar/Projects/mcp_creation_test/.venv/bin/python
    args:
      - /Users/dineshkumar/Projects/mcp_creation_test/backend/mcp_server.py
```

In this workspace, the config file currently used is:

```text
.continue/mcpServers/new-mcp-server-1.yaml
```

Connection steps:

1. Save the MCP config in the active Continue config file.
2. Restart Continue or reload VS Code.
3. Make sure the server starts with the repo Python environment.
4. Ask for a slot lookup or booking in natural language.

Example prompts that should trigger the MCP tools:

- get test details available in Bangalore
- list test slots in Chennai on 2026-07-20
- book the Bangalore academic slot for this candidate

If Continue is connected correctly, it should call:

- `list_test_slots`
- `get_test_slot`
- `book_test_slot`

## Startup Flow

Typical local setup looks like this:

1. Start PostgreSQL
2. Run Alembic migrations
3. Start the FastAPI app or MCP server

Example:

```bash
docker compose up -d
cd backend
alembic upgrade head
```

To run the MCP server:

```bash
./.venv/bin/python backend/mcp_server.py
```

## Seed Data

The database starts with three test slots:

- Chennai, IDP Chennai Anna Salai, Academic, 2026-07-20, 09:00, 15 seats
- Chennai, IDP Chennai Anna Salai, General, 2026-07-20, 14:00, 8 seats
- Bangalore, IDP Bangalore MG Road, Academic, 2026-07-20, 09:00, 12 seats

These are loaded through Alembic so every environment can be recreated consistently.

## Why This Setup Is Useful

This repo gives you:

- reproducible local database setup
- a clear migration path
- a small but production-friendly FastAPI layer
- an MCP server for tool-based workflows
- a shared source of truth for both API surfaces

## Where To Look First

- database schema: `backend/app/db/models.py`
- HTTP routes: `backend/app/main.py`
- MCP tools: `backend/mcp_server.py`
- migrations: `backend/migrations/versions`
- run instructions: `README.md`
