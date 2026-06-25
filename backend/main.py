import json
import os
import shutil
import subprocess
import zoneinfo
from datetime import date, datetime
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

RECEIPTS_DIR = Path(os.getenv("RECEIPTS_DIR", "/app/receipts"))
SETTINGS_FILE = Path(os.getenv("DATA_DIR", "/app/data")) / "settings.json"


def _load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_settings(data: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data))

from database import SessionLocal
import crud
from schemas import (
    AccountCreate, AccountOut,
    CategoryCreate, CategoryOut,
    TransactionCreate, TransactionOut,
    RecurringTransactionCreate, RecurringTransactionOut,
    MonthlySummary, AccountBalance, CategoryTotal,
    TransactionType,
    BudgetCreate, BudgetOut,
    SettingsUpdate,
)
from init import init_db


def _get_timezone() -> str:
    tz = _load_settings().get("timezone") or os.getenv("SCHEDULER_TIMEZONE", "UTC")
    try:
        zoneinfo.ZoneInfo(tz)
    except zoneinfo.ZoneInfoNotFoundError:
        raise RuntimeError(f"Invalid timezone '{tz}'. Use a valid IANA name e.g. 'America/Toronto'.")
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
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    _run_processor()
    scheduler.add_job(_run_processor, "cron", hour=0, minute=0, timezone=_get_timezone(), id="daily_processor")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    tx_type: TransactionType | None = Query(default=None, alias="type"),
    start_date: date | None = None,
    end_date: date | None = None,
    min_amount: float | None = Query(default=None, gt=0),
    max_amount: float | None = Query(default=None, gt=0),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.read_transactions_filtered(db, account_id, category_id, tx_type, start_date, end_date, min_amount, max_amount, limit, offset)

@app.put("/transactions/{tx_id}")
def update_transaction_endpoint(tx_id: int, tx: TransactionCreate, db: Session = Depends(get_db)):
    updated = crud.update_transaction(tx_id, tx, db)
    if updated == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"updated": updated}

@app.delete("/transactions/{tx_id}")
def delete_transaction_endpoint(tx_id: int, db: Session = Depends(get_db)):
    tx = crud.get_transaction(db, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.receipt_path:
        receipt_file = RECEIPTS_DIR / tx.receipt_path
        if receipt_file.exists():
            receipt_file.unlink()
    deleted = crud.delete_transaction(tx_id, db)
    return {"deleted": deleted}

@app.post("/transactions/{tx_id}/receipt")
def upload_receipt(tx_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    tx = crud.get_transaction(db, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    if tx.receipt_path:
        old = RECEIPTS_DIR / tx.receipt_path
        if old.exists():
            old.unlink()
    suffix = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{tx_id}{suffix}"
    with (RECEIPTS_DIR / filename).open("wb") as f:
        shutil.copyfileobj(file.file, f)
    crud.set_receipt_path(db, tx_id, filename)
    return {"receipt_path": filename}

@app.get("/transactions/{tx_id}/receipt")
def download_receipt(tx_id: int, db: Session = Depends(get_db)):
    tx = crud.get_transaction(db, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not tx.receipt_path:
        raise HTTPException(status_code=404, detail="No receipt attached")
    path = RECEIPTS_DIR / tx.receipt_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="Receipt file not found")
    return FileResponse(path)

@app.delete("/transactions/{tx_id}/receipt")
def delete_receipt_endpoint(tx_id: int, db: Session = Depends(get_db)):
    tx = crud.get_transaction(db, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not tx.receipt_path:
        raise HTTPException(status_code=404, detail="No receipt attached")
    path = RECEIPTS_DIR / tx.receipt_path
    if path.exists():
        path.unlink()
    crud.set_receipt_path(db, tx_id, None)
    return {"deleted": True}


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

@app.get("/summary/upcoming", response_model=list[RecurringTransactionOut])
def upcoming_recurring_endpoint(days: int = Query(default=7, ge=1, le=90), db: Session = Depends(get_db)):
    return crud.get_upcoming_recurring(db, days)


@app.get("/budgets", response_model=list[BudgetOut])
def get_budgets_endpoint(db: Session = Depends(get_db)):
    return crud.get_budgets(db)

@app.post("/budgets", response_model=BudgetOut)
def upsert_budget_endpoint(budget: BudgetCreate, db: Session = Depends(get_db)):
    return crud.upsert_budget(db, budget.category_id, budget.amount)

@app.delete("/budgets/{budget_id}")
def delete_budget_endpoint(budget_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_budget(db, budget_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Budget not found")
    return {"deleted": deleted}


@app.get("/settings")
def get_settings():
    return {"timezone": _get_timezone()}

@app.patch("/settings")
def update_settings(payload: SettingsUpdate):
    try:
        zoneinfo.ZoneInfo(payload.timezone)
    except zoneinfo.ZoneInfoNotFoundError:
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {payload.timezone}")
    settings = _load_settings()
    settings["timezone"] = payload.timezone
    _save_settings(settings)
    scheduler.reschedule_job("daily_processor", trigger="cron", hour=0, minute=0, timezone=payload.timezone)
    return {"timezone": payload.timezone}


@app.get("/backup/db")
def backup_db():
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    pg_url = db_url.replace("+psycopg2", "").replace("+asyncpg", "")
    result = subprocess.run(
        ["pg_dump", "--no-owner", "--no-acl", pg_url],
        capture_output=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr.decode())
    filename = f"budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    return Response(
        content=result.stdout,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )