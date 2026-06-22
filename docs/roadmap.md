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

## What's Next (Later)
|    Phase    | Description                                |
|-------------|--------------------------------------------|
| **Phase 4** | Automated tables (CRUD for tables) & time  |
| **Phase 5** | Android app                                |
| **Phase 6** | Deploy to server                           |
