# Budgeting App - Roadmap

**Stack:** Kotlin (Android) + FastAPI (Python) + PostgreSQL  
**Goal:** Track income and expenses on mobile, synced to your own server.

---

## MVP Goal

When done, you'll be able to:
- Add/edit transactions (income & expenses)
- Organize by accounts (cards, cash) and categories
- See monthly summaries
- View transaction history

---

## Phase 1: Backend Setup (Complete)

### Step 1: Get FastAPI Running
- [X] Create FastAPI app (`main.py`)
- [X] Add `/health` endpoint
- [X] Run locally and see it working

### Step 2: Database Connection
- [X] Install PostgreSQL (or use local/cloud)
- [X] Connect FastAPI to database
- [X] Test connection works

### Step 3: Basic Transaction CRUD
- [X] Create a method to add to table
- [X] Create a method to read table contents
- [X] Create a method to update content from table
- [X] Create a method to delete content from table

### Step 4: Finalize Transaction Data Format
- [X] Finalize JSON format (what the Android app sends/receives)
- [X] Update Functions & table columns to match the finalized format

### Step 5: Database Models
- [X] Create Account model
- [X] Create Category model
- [X] Create Transaction model

### Step 6: One Simple Endpoint
- [X] Create endpoint to add a transaction (no auth yet)
- [X] Test it works
- [X] See data in database

---

## Phase 2: Database Initializer (Complete)

Create a repeatable way to set up the database and tables so the app (and new environments) can run reliably.

### Step 1: Create tables from models
- [X] Import `Base` and all models where metadata is registered
- [X] Call `Base.metadata.create_all(bind=engine)` (e.g. in a script or at app startup)
- [X] Verify `accounts`, `categories`, and `transactions` tables exist in PostgreSQL

### Step 2: Add an initializer entry point
- [X] Add a script or CLI command (e.g. `python -m backend.init_db` or `init_db.py`) that creates all tables
- [X] Document in README how to run it (e.g. "Run once before first use" or "Run after cloning")

### Step 3: Ensure database exists
- [X] Document that the PostgreSQL database must exist (e.g. created manually or via `createdb`)
- [X] Optionally: add a small script that creates the database if it does not exist (using settings from `local_settings`)

### Step 4: Docker Containerization
- [X] Add docker-compose.yml
- [X] Add backend Dockerfile
- [X] Configure Postgres container
- [X] Verify stack runs with one command

### Step 5: Seed or migrate
- [X] If needed: seed default data (e.g. default categories) in the initializer or a separate seed script
- [X] For later: plan for migrations (e.g. Alembic) when you change table schemas

---

## Phase 3: Core API Expansion (Current Focus)

Goal: Make the backend usable for the Android client by completing CRUD + adding practical query support.

### Step 1: Accounts CRUD (Finish)
- [X] Create account
- [X] List accounts
- [X] Delete account
- [X] Update account (rename)

### Step 2: Categories CRUD (Finish)
- [X] Create category
- [X] List categories
- [X] Delete category
- [X] Update category (rename)

### Step 3: Transactions API (Make usable)
- [X] Create transaction
- [X] List transactions
- [X] Delete transaction
- [X] Update transaction
- [X] Add filters to list transactions (account/category/date range)
- [X] Add pagination (limit/offset)

### Step 4: Recurring Transactions API (Finish)
- [X] Create recurring transaction
- [X] List recurring transactions
- [X] Delete recurring transaction
- [X] Update recurring transaction

### Step 5: Documentation polish
- [X] Document Phase 3 endpoints in README (brief list + examples)

---

## Phase 4: Automation & Summaries

Goal: Make recurring transactions run themselves, expose the missing filter endpoint, and add time-based summary data for the web dashboard.

### Step 1: Recurring Transaction Processor (Core Logic)
- [X] Write a `process_due_recurring_transactions(db)` function in `crud.py`
- [X] Query all `recurring_transactions` where `next_run_date <= today`
- [X] For each one: create a real `Transaction` and advance `next_run_date` by the interval (`+1 day / +7 days / +1 month / +1 year`)

### Step 2: Expose the Processor via Endpoint
- [X] Add `POST /recurring_transactions/run` endpoint in `main.py`
- [X] Returns count of transactions created
- [X] Also call it automatically on app startup (in `lifespan`) so it runs each time the container starts

### Step 3: Wire Up Recurring Transaction Filters
- [X] Replace `read_recurring_transactions` call in `main.py` with `read_recurring_transactions_filtered` (already in `crud.py`, just not hooked up)
- [X] Add query params to `GET /recurring_transactions`: `account_id`, `category_id`, `recurring_interval`, `start_date`, `end_date`, `limit`, `offset`

### Step 4: Summary / Aggregation Endpoints
- [X] Add `GET /summary/monthly?year=YYYY&month=MM` → returns `{total, transaction_count}` for that month
- [X] Add `GET /summary/accounts` → returns current balance (sum of all transactions) per account
- [X] Add `GET /summary/categories?year=YYYY&month=MM` → returns spending per category for the month

### Step 5: Tests & Documentation
- [X] Write tests for the recurring transaction processor (due today, not yet due, interval advancement for all 4 interval types)
- [X] Write tests for the summary endpoints
- [X] Update README with new endpoints

---

## Phase 5: Model Expansion (Current Focus)

Goal: Extend the transaction model to support income/expense distinction and receipt attachments before building the frontend.

### Step 1: Income/Expense Type
- [X] Add `type` enum (`income` / `expense`) to `Transaction` model and schema (required, amount stays positive and non-zero)
- [X] Add `type` field to `RecurringTransaction` model and schema
- [X] Generate and apply Alembic migration
- [X] Update summary endpoints to split income vs expenses (`total_income`, `total_expenses`, `net`)

### Step 2: Receipt Attachments
- [ ] Add nullable `receipt_path` column to `Transaction` model
- [ ] Add `POST /transactions/{id}/receipt` endpoint (accepts image upload, stores in Docker volume)
- [ ] Add `GET /transactions/{id}/receipt` endpoint (returns the image file)
- [ ] Mount a `receipts` volume in `docker-compose.yml`
- [ ] Generate and apply Alembic migration

### Step 3: Tests & Documentation
- [ ] Update existing transaction tests to include `type` field
- [ ] Write tests for receipt upload and retrieval
- [ ] Update README with new fields and endpoints

---

## Phase 6: Web Frontend

Goal: Build a browser-based UI served by the same Docker stack. Accessible from any device on the network at `http://server-ip`.

### Step 1: CORS & Project Structure
- [ ] Add CORS middleware to FastAPI so the frontend can call the API
- [ ] Create `frontend/` directory with `index.html`, `css/style.css`, `js/app.js`
- [ ] Add Alpine.js via CDN (no npm, no build step)

### Step 2: Docker Integration
- [ ] Add nginx container to `docker-compose.yml` to serve the `frontend/` directory
- [ ] Verify frontend is accessible at port 80 after `docker compose up`

### Step 3: Base Layout & Navigation
- [ ] Build a base layout with a sidebar/navbar (Transactions, Accounts, Categories, Recurring, Dashboard)
- [ ] Implement client-side view switching with Alpine.js (single page, no page reloads)

### Step 4: Transactions View
- [ ] List transactions with filters (account, category, date range, type, pagination)
- [ ] Saveable/pinned filters via `localStorage` so they persist across refreshes
- [ ] Add transaction form (with income/expense toggle and optional receipt upload)
- [ ] Edit and delete transaction

### Step 5: Accounts & Categories Views
- [ ] List, add, rename, delete accounts
- [ ] List, add, rename, delete categories

### Step 6: Recurring Transactions View
- [ ] List recurring transactions with filters
- [ ] Add, edit, delete recurring transaction
- [ ] Manual "Run Now" button (`POST /recurring_transactions/run`)

### Step 7: Dashboard View
- [ ] Month picker (year + month)
- [ ] Monthly summary (total income, total expenses, net)
- [ ] Account balances
- [ ] Category breakdown for selected month

### Step 8: Settings Page
- [ ] Add a settings view in the UI
- [ ] Timezone selector dropdown (updates `SCHEDULER_TIMEZONE` in `.env`)

### Step 9: Setup Script
- [ ] Write `start.sh` for Linux that auto-installs Docker if missing, copies `.env.example` to `.env` if not present, and runs `docker compose up -d`
- [ ] Test on Ubuntu

### Step 10: Documentation
- [ ] Update README with frontend access instructions and setup script usage

---

## What's Next (Later)
|    Phase    | Description           |
|-------------|-----------------------|
| **Phase 6** | Web Frontend          |
|-------------|-----------------------|
| **Phase 7** | Deploy to server      |
