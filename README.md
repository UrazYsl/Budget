# Budgeting-App

A full-stack personal budgeting app with a FastAPI backend and an Android client (Kotlin). Tracks income, expenses, accounts, and categories with REST APIs and sync to your own server.

**Stack:** Kotlin (Android), FastAPI (Python), PostgreSQL, Docker

## Status

- **Phase 1 (Backend setup):** Complete - FastAPI app, DB connection, CRUD, schemas, database models (Account, Category, Transaction), and transaction endpoint.
- **Phase 2 (Environment & Initialization):** Complete - Docker integration and reproducible database setup.
- **Phase 3 (Core API Expansion):** In Progress — completing update endpoints and improving transaction querying.

## Python packages

- fastapi
- uvicorn
- sqlalchemy
- psycopg[binary]
- alembic

OPTIONALS:
- pytest

## Prerequisites

### Installing Docker

**Windows**
1. Download and install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Start Docker Desktop and wait for it to finish loading before running any commands

**macOS**
1. Download and install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Start Docker Desktop and wait for it to finish loading

**Linux (Ubuntu/Debian)**
```bash
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER
newgrp docker
```

> After installing, close and reopen your terminal (or run `newgrp docker`) before running `docker compose`.

- Docker must be running before executing `docker compose up`
- You do not need to log into Docker or create any database manually.

If you get:
```
permission denied while trying to connect to the Docker daemon socket
```

Run:
```bash
sudo usermod -aG docker $USER
newgrp docker
```
Or log out and log back in.


## Environment Configuration

The project uses a `.env` file for database configuration.

Create a `.env` file in the project root based on `.env.example`:

```bash
cp .env.example .env
```
Then adjust the values if needed (database name, user, password).
Docker Compose automatically loads variables from .env.


### Run the full stack

From the project root:

```bash
docker compose up --build
```
This will:
- Start a PostgreSQL container
- Build and start the FastAPI backend
- Automatically apply Alembic migrations (create/update tables)


## Database & migrations

This project uses **Alembic** for schema management.

When you run:

```bash
docker compose up --build
```
The backend automatically runs alembic upgrade head on startup.


## If You Change Database Models

1) Generate a new migration:
```bash
docker compose run --rm api alembic revision --autogenerate -m "describe change"
```

2) Apply it:
```bash
docker compose run --rm api alembic upgrade head
```

Migration files are stored in `backend/alembic/versions/` and should be committed to version control.

### API Docs
http://127.0.0.1:8000/docs

### Health Check
http://127.0.0.1:8000/health/db

### Stop containers

```bash
docker compose down
```

### Reset database
```bash
docker compose down -v
docker compose up --build
```

## Running Tests

Tests use a separate `budgeting_test` database inside the same PostgreSQL container.

**One-time setup** — create the test database (only needed once, survives restarts):
```bash
docker exec budgeting-app-db-1 psql -U postgres -c "CREATE DATABASE budgeting_test;"
```

**Start** (same as normal — tests share the running container):
```bash
docker compose up -d
```

**Run tests:**
```bash
cd backend
python -m pytest tests/ -v
```

**Stop:**
```bash
docker compose down
```

> If you wipe the volume with `docker compose down -v`, you'll need to recreate the test database again.

See [docs/roadmap.md](docs/roadmap.md) for the full development plan.

