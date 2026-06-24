# Design Decisions

Brief explanations for non-obvious choices made throughout the project.

---

## Backend

**FastAPI over Flask/Django**
FastAPI has automatic Swagger docs, native async support, and Pydantic validation built in. Flask needs extra libraries for all of that. Django is overkill for a personal API.

**PostgreSQL over SQLite**
SQLite doesn't support `ON DELETE SET DEFAULT` (needed for reassigning transactions to Misc when a category is deleted) or proper concurrent access. PostgreSQL does both.

**SQLAlchemy over raw SQL**
Keeps queries Pythonic and safe from SQL injection. Works seamlessly with FastAPI and Alembic.

**Alembic for migrations**
Schema changes need to be applied to the running database without wiping data. Alembic handles this automatically on `docker compose up`.

**`pool_pre_ping=True` in SQLAlchemy engine**
The connection pool can hold stale connections after long idle periods. `pool_pre_ping` transparently reconnects before each query so the server never errors after sitting idle.

**Timezone configured via `.env`, not hardcoded**
Different users are in different timezones. `SCHEDULER_TIMEZONE` in `.env` lets each person set their own without touching code. Defaults to `UTC` if not set.

**`python-dateutil` for date arithmetic**
`timedelta` can't handle months/years correctly (e.g. Jan 31 + 1 month). `relativedelta` from `python-dateutil` handles edge cases like month-end dates properly.

---

## Scheduling

**APScheduler over FastAPI BackgroundTasks / Celery**
`BackgroundTasks` runs after a request — it's not a scheduler, it can't run on a timer. Celery requires Redis and a separate worker process, which is overkill. APScheduler runs inside the FastAPI process with no extra infrastructure.

**Toronto timezone (`America/Toronto`) for the daily job**
The server will be hosted in Toronto. `America/Toronto` automatically handles EST/EDT daylight saving switches.

**Also run processor on startup**
If the server is down at midnight, missed recurring transactions would never process. Running on every startup catches them up regardless of downtime.

---

## Infrastructure

**Docker over manual install**
Guarantees identical environment on any machine (Windows or Linux). One command (`docker compose up`) starts everything.

**`restart: unless-stopped` on both containers**
Containers restart automatically after a crash or server reboot, but stay down if manually stopped with `docker compose down`.

**Test database created automatically in `tester_db_setup.py`**
Requiring a manual `CREATE DATABASE` command breaks the "clone and run" goal. The test setup now creates it automatically if it doesn't exist.

---

## Frontend

**Web UI over Android app**
A browser-based UI works on every device (phone, tablet, desktop) with no installation. An Android app would only work on Android and requires a build/publish pipeline.

**Income/expense as a `type` field, not signed amounts**
Allowing negative numbers is confusing UX — a user entering `-42.50` for an expense is error-prone. Instead, the user picks `income` or `expense` and always enters a positive amount. Zero is not allowed as it's meaningless as either. The app handles the math.

**No per-transaction currency**
Amounts are stored as plain numbers. A single `CURRENCY_SYMBOL` in `.env` (e.g. `$`) is displayed by the frontend everywhere. No exchange rates, no per-transaction currency field — too much complexity for a personal app used in one currency.

**Receipts stored on disk, not in the database**
Storing binary files in PostgreSQL (as BLOBs) bloats the database and makes backups heavy. Files are stored in a Docker volume on the server filesystem, with only the file path saved in the database.

**Alpine.js + plain HTML over React / Vue / HTMX**
- React requires npm and a build step — too much overhead for a personal app.
- Vue via CDN is clean but slightly more complex than needed.
- HTMX would require adding HTML-returning endpoints to FastAPI (extra backend work).
- Alpine.js adds reactivity directly to HTML with a single `<script>` tag. No npm, no build, no extra backend changes.

**nginx to serve the frontend**
Static files need a web server. nginx is lightweight, standard, and trivial to add as a Docker container.
