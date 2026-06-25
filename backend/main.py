import os
import zoneinfo
from datetime import date
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import SessionLocal
import crud
from schemas import (
    AccountCreate, AccountOut,
    CategoryCreate, CategoryOut,
    TransactionCreate, TransactionOut,
    RecurringTransactionCreate, RecurringTransactionOut,
    MonthlySummary, AccountBalance, CategoryTotal,
    TransactionType,
)
from init import init_db


def _get_timezone() -> str:
    tz = os.getenv("SCHEDULER_TIMEZONE", "UTC")
    try:
        zoneinfo.ZoneInfo(tz)
    except zoneinfo.ZoneInfoNotFoundError:
        raise RuntimeError(f"Invalid SCHEDULER_TIMEZONE '{tz}'. Use a valid tz name e.g. 'America/Toronto'.")
    return tz


def _run_processor():
    db = SessionLocal()
    try:
        crud.process_due_recurring_transactions(db)
    finally:
        db.close()


scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _run_processor()
    scheduler.add_job(_run_processor, "cron", hour=0, minute=0, timezone=_get_timezone())
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    return {"ok": db.execute(text("select 1")).scalar_one() == 1}


@app.post("/accounts", response_model=AccountOut)
def create_account_endpoint(account: AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(account, db)

@app.get("/accounts", response_model=list[AccountOut])
def read_accounts_endpoint(db: Session = Depends(get_db)):
    return crud.read_accounts(db)

@app.put("/accounts/{account_id}")
def update_account_endpoint(account_id: int, new_name: str, db: Session = Depends(get_db)):
    updated = crud.update_account(account_id, new_name, db)
    if updated == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"updated": updated}

@app.delete("/accounts/{account_id}")
def delete_account_endpoint(account_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_account(account_id, db)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"deleted": deleted, "warning": "Associated transactions were deleted (cascade)."}


@app.post("/categories", response_model=CategoryOut)
def create_category_endpoint(category: CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(category, db)

@app.get("/categories", response_model=list[CategoryOut])
def read_categories_endpoint(db: Session = Depends(get_db)):
    return crud.read_categories(db)

@app.put("/categories/{category_id}")
def update_category_endpoint(category_id: int, new_name: str, db: Session = Depends(get_db)):
    updated = crud.update_category(category_id, new_name, db)
    if updated == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"updated": updated}

@app.delete("/categories/{category_id}")
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_category(category_id, db)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"deleted": deleted, "note": "Transactions were reassigned to Misc (default category)."}


@app.post("/transactions", response_model=TransactionOut)
def create_transaction_endpoint(tx: TransactionCreate, db: Session = Depends(get_db)):
    return crud.create_transaction(tx, db)

@app.get("/transactions", response_model=list[TransactionOut])
def read_transactions_endpoint(
    account_id: int | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.read_transactions_filtered(db, account_id, category_id, start_date, end_date, limit, offset)

@app.put("/transactions/{tx_id}")
def update_transaction_endpoint(tx_id: int, tx: TransactionCreate, db: Session = Depends(get_db)):
    updated = crud.update_transaction(tx_id, tx, db)
    if updated == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"updated": updated}

@app.delete("/transactions/{tx_id}")
def delete_transaction_endpoint(tx_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_transaction(tx_id, db)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"deleted": deleted}


@app.post("/recurring_transactions", response_model=RecurringTransactionOut)
def create_recurring_transaction_endpoint(rtx: RecurringTransactionCreate, db: Session = Depends(get_db)):
    return crud.create_recurring_transaction(rtx, db)

@app.get("/recurring_transactions", response_model=list[RecurringTransactionOut])
def read_recurring_transactions_endpoint(
    account_id: int | None = None,
    category_id: int | None = None,
    recurring_interval: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.read_recurring_transactions_filtered(db, account_id, category_id, recurring_interval, start_date, end_date, limit, offset)

@app.put("/recurring_transactions/{rtx_id}")
def update_recurring_transaction_endpoint(rtx_id: int, rtx: RecurringTransactionCreate, db: Session = Depends(get_db)):
    updated = crud.update_recurring_transaction(rtx_id, rtx, db)
    if updated == 0:
        raise HTTPException(status_code=404, detail="Recurring transaction not found")
    return {"updated": updated}

@app.delete("/recurring_transactions/{rtx_id}")
def delete_recurring_transaction_endpoint(rtx_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_recurring_transaction(rtx_id, db)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Recurring transaction not found")
    return {"deleted": deleted}

@app.post("/recurring_transactions/run")
def run_recurring_transactions_endpoint(db: Session = Depends(get_db)):
    count = crud.process_due_recurring_transactions(db)
    return {"created": count}


@app.get("/summary/monthly", response_model=MonthlySummary)
def monthly_summary_endpoint(year: int, month: int, db: Session = Depends(get_db)):
    return crud.get_monthly_summary(db, year, month)

@app.get("/summary/accounts", response_model=list[AccountBalance])
def account_balances_endpoint(db: Session = Depends(get_db)):
    return crud.get_account_balances(db)

@app.get("/summary/categories", response_model=list[CategoryTotal])
def category_totals_endpoint(year: int, month: int, db: Session = Depends(get_db)):
    return crud.get_category_totals(db, year, month)