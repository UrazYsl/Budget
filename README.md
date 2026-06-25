# Budgeting-App

A self-hosted personal budgeting web app. FastAPI backend + Alpine.js frontend, served via Docker. Accessible from any browser on your network.

**Stack:** FastAPI (Python), PostgreSQL, Alpine.js, HTML/CSS, nginx, Docker

## Status

- **Phase 1 (Backend setup):** Complete - FastAPI app, DB connection, CRUD, schemas, database models (Account, Category, Transaction), and transaction endpoint.
- **Phase 2 (Environment & Initialization):** Complete - Docker integration and reproducible database setup.
- **Phase 3 (Core API Expansion):** Complete — full CRUD for accounts, categories, transactions, and recurring transactions with filtering and pagination.
- **Phase 4 (Automation & Summaries):** Complete — recurring transaction processor with APScheduler (runs daily at midnight Toronto time + on startup), summary endpoints for monthly totals, account balances, and category breakdowns.
- **Phase 5 (Model Expansion):** Complete — income/expense `type` field on transactions and recurring transactions, receipt image attachments.
- **Phase 6 (Web Frontend):** In progress — Alpine.js + HTML/CSS frontend served via nginx in Docker.
- **Phase 7 (Styling):** Planned — visual polish pass on the frontend.
- **Phase 8 (Deploy):** Planned — deploy to Ubuntu home server with setup script.

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

A `.env` file is optional, the app runs with defaults if none is present. It is recommended if you want to change the password or set your timezone.

To create one:

```bash
cp .env.example .env
```

Then adjust the values:

| Variable | Description |
|----------|-------------|
| `POSTGRES_USER` | Database username |
| `POSTGRES_PASSWORD` | Database password **change this** |
| `POSTGRES_DB` | Database name |
| `DATABASE_URL` | Full DB connection string (update user/password to match above) |
| `TEST_DATABASE_URL` | Test DB connection string (same but points to `budgeting_test`) |
| `SCHEDULER_TIMEZONE` | Timezone for the daily recurring transaction job (e.g. `America/Toronto`, `Europe/Istanbul`, `UTC`) |

Docker Compose automatically loads variables from `.env`.


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

## API Endpoints

Interactive docs (Swagger UI): http://127.0.0.1:8000/docs

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health/db` | Check database connectivity |

### Accounts

| Method | Path | Description |
|--------|------|-------------|
| POST | `/accounts` | Create an account |
| GET | `/accounts` | List all accounts |
| PUT | `/accounts/{id}?new_name=X` | Rename an account |
| DELETE | `/accounts/{id}` | Delete account (cascades transactions) |

```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Checking"}'
```

### Categories

| Method | Path | Description |
|--------|------|-------------|
| POST | `/categories` | Create a category |
| GET | `/categories` | List all categories |
| PUT | `/categories/{id}?new_name=X` | Rename a category |
| DELETE | `/categories/{id}` | Delete category (transactions reassigned to Misc) |

```bash
curl -X POST http://localhost:8000/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Groceries"}'
```

### Transactions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/transactions` | Create a transaction |
| GET | `/transactions` | List transactions (supports filters) |
| PUT | `/transactions/{id}` | Update a transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |

**GET query parameters (all optional):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `account_id` | int | Filter by account |
| `category_id` | int | Filter by category |
| `start_date` | date (YYYY-MM-DD) | Earliest date (inclusive) |
| `end_date` | date (YYYY-MM-DD) | Latest date (inclusive) |
| `limit` | int | Max results to return |
| `offset` | int | Number of results to skip (default 0) |

**Transaction fields:**

| Field | Type | Description |
|-------|------|-------------|
| `date` | date (YYYY-MM-DD) | Transaction date |
| `amount` | float (> 0) | Always positive |
| `type` | `income` or `expense` | Whether this is income or an expense |
| `account_id` | int | Account the transaction belongs to |
| `category_id` | int | Category for this transaction |

```bash
# Create
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"amount": 42.50, "date": "2026-06-01", "type": "expense", "account_id": 1, "category_id": 2}'

# List with filters
curl "http://localhost:8000/transactions?account_id=1&start_date=2026-01-01&end_date=2026-06-30&limit=20&offset=0"
```

### Transaction Receipts

| Method | Path | Description |
|--------|------|-------------|
| POST | `/transactions/{id}/receipt` | Upload a receipt image (replaces existing) |
| GET | `/transactions/{id}/receipt` | Download the receipt image |
| DELETE | `/transactions/{id}/receipt` | Remove the receipt |

Only image files are accepted (`image/*` content type). The `receipt_path` field on a transaction is `null` if no receipt has been uploaded.

```bash
# Upload
curl -X POST http://localhost:8000/transactions/1/receipt \
  -F "file=@/path/to/receipt.jpg"

# Download
curl http://localhost:8000/transactions/1/receipt --output receipt.jpg
```

### Recurring Transactions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/recurring_transactions` | Create a recurring transaction |
| GET | `/recurring_transactions` | List all recurring transactions |
| PUT | `/recurring_transactions/{id}` | Update a recurring transaction |
| DELETE | `/recurring_transactions/{id}` | Delete a recurring transaction |

**GET query parameters (all optional):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `account_id` | int | Filter by account |
| `category_id` | int | Filter by category |
| `recurring_interval` | string | Filter by interval (`daily`, `weekly`, `monthly`, `yearly`) |
| `start_date` | date (YYYY-MM-DD) | Earliest next_run_date (inclusive) |
| `end_date` | date (YYYY-MM-DD) | Latest next_run_date (inclusive) |
| `limit` | int | Max results to return |
| `offset` | int | Number of results to skip (default 0) |

`recurring_interval` accepted values: `daily`, `weekly`, `monthly`, `yearly`

```bash
# Create
curl -X POST http://localhost:8000/recurring_transactions \
  -H "Content-Type: application/json" \
  -d '{"amount": 9.99, "type": "expense", "recurring_interval": "monthly", "next_run_date": "2026-07-01", "account_id": 1, "category_id": 2}'

# Update
curl -X PUT http://localhost:8000/recurring_transactions/1 \
  -H "Content-Type: application/json" \
  -d '{"amount": 12.99, "type": "expense", "recurring_interval": "monthly", "next_run_date": "2026-07-01", "account_id": 1, "category_id": 2}'
```

### Recurring Transaction Processor

| Method | Path | Description |
|--------|------|-------------|
| POST | `/recurring_transactions/run` | Process all due recurring transactions now |

Returns `{"created": N}` — the number of real transactions created. Also runs automatically on startup and daily at midnight (Toronto time).

### Summaries

| Method | Path | Description |
|--------|------|-------------|
| GET | `/summary/monthly` | Total income, total expenses, net, and count for a given month |
| GET | `/summary/accounts` | Running balance per account |
| GET | `/summary/categories` | Spend per category for a given month |

**GET `/summary/monthly` query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | int | Year (e.g. 2026) |
| `month` | int | Month (1–12) |

**GET `/summary/categories` query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | int | Year (e.g. 2026) |
| `month` | int | Month (1–12) |

```bash
# Monthly summary
curl "http://localhost:8000/summary/monthly?year=2026&month=6"

# Account balances
curl "http://localhost:8000/summary/accounts"

# Category breakdown for a month
curl "http://localhost:8000/summary/categories?year=2026&month=6"
```

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

> **Python packages** — inside Docker all packages install automatically. For running tests locally on your machine you need to install them manually once:
> ```bash
> python3 -m pip install fastapi uvicorn sqlalchemy "psycopg[binary]" alembic python-dateutil apscheduler python-multipart pytest python-dotenv
> ```

**Start** (same as normal, tests share the running container):
```bash
docker compose up -d
```

**Run tests:**
```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/crud_tests/test_transactions.py -v

# Run a specific test by name (substring match)
python -m pytest tests/ -v -k "test_update_transaction"

# Run and stop at the first failure
python -m pytest tests/ -v -x

# Run without verbose output (summary only)
python -m pytest tests/
```

Test files are in `backend/tests/crud_tests/`:

| File | What it covers |
|------|----------------|
| `test_accounts.py` | Account CRUD |
| `test_categories.py` | Category CRUD |
| `test_transactions.py` | Transaction CRUD |
| `test_recurring_transactions.py` | Recurring transaction CRUD |
| `test_filter.py` | Transaction filtering & pagination |
| `test_filter_recurring.py` | Recurring transaction filtering & pagination |
| `test_receipts.py` | Receipt path CRUD (`get_transaction`, `set_receipt_path`) |

**Stop:**
```bash
docker compose down
```

> If you wipe the volume with `docker compose down -v`, you'll need to recreate the test database again.

See [docs/roadmap.md](docs/roadmap.md) for the full development plan and [docs/decisions.md](docs/decisions.md) for design decisions and the reasoning behind them.

