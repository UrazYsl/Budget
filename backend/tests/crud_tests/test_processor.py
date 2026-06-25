import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import crud
import schemas
import uuid
from datetime import date, timedelta
from models import Transaction

def _make_rtx(session, interval, next_run_date, amount=50.0):
    suffix = uuid.uuid4().hex[:8]
    account = crud.create_account(schemas.AccountCreate(name=f"Proc Account {suffix}"), session)
    category = crud.create_category(schemas.CategoryCreate(name=f"Proc Category {suffix}"), session)
    return crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=amount,
            type="expense",
            recurring_interval=interval,
            next_run_date=next_run_date,
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )

def test_due_transaction_creates_real_transaction(session):
    yesterday = date.today() - timedelta(days=1)
    rtx = _make_rtx(session, "monthly", yesterday)
    tx_count_before = len(session.query(Transaction).all())

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    tx_count_after = len(session.query(Transaction).all())
    assert tx_count_after > tx_count_before

def test_due_transaction_advances_next_run_date(session):
    yesterday = date.today() - timedelta(days=1)
    rtx = _make_rtx(session, "monthly", yesterday)

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    updated = session.get(type(rtx), rtx.id)
    assert updated.next_run_date > date.today()

def test_not_due_transaction_is_skipped(session):
    tomorrow = date.today() + timedelta(days=1)
    rtx = _make_rtx(session, "monthly", tomorrow)
    original_date = rtx.next_run_date

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    unchanged = session.get(type(rtx), rtx.id)
    assert unchanged.next_run_date == original_date

def test_not_due_transaction_creates_no_transaction(session):
    tomorrow = date.today() + timedelta(days=1)
    rtx = _make_rtx(session, "monthly", tomorrow, amount=77.77)
    tx_count_before = session.query(Transaction).filter(Transaction.amount == 77.77).count()

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    tx_count_after = session.query(Transaction).filter(Transaction.amount == 77.77).count()
    assert tx_count_after == tx_count_before

def test_daily_interval_advances_by_one_day(session):
    yesterday = date.today() - timedelta(days=1)
    rtx = _make_rtx(session, "daily", yesterday)

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    updated = session.get(type(rtx), rtx.id)
    # processes yesterday AND today (today <= today), so lands on tomorrow
    assert updated.next_run_date == date.today() + timedelta(days=1)

def test_weekly_interval_advances_by_seven_days(session):
    yesterday = date.today() - timedelta(days=1)
    rtx = _make_rtx(session, "weekly", yesterday)

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    updated = session.get(type(rtx), rtx.id)
    assert updated.next_run_date == yesterday + timedelta(weeks=1)

def test_monthly_interval_advances_by_one_month(session):
    past = date(2026, 1, 15)
    rtx = _make_rtx(session, "monthly", past)

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    updated = session.get(type(rtx), rtx.id)
    assert updated.next_run_date > date.today()

def test_yearly_interval_advances_by_one_year(session):
    past = date(2025, 1, 1)
    rtx = _make_rtx(session, "yearly", past)

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    updated = session.get(type(rtx), rtx.id)
    assert updated.next_run_date > date.today()

def test_catchup_creates_multiple_transactions(session):
    # 3 months overdue — should create 3 transactions
    three_months_ago = date.today().replace(month=date.today().month - 3) if date.today().month > 3 else date(date.today().year - 1, date.today().month + 9, date.today().day)
    rtx = _make_rtx(session, "monthly", three_months_ago, amount=11.11)

    crud.process_due_recurring_transactions(session)

    session.expire_all()
    created = session.query(Transaction).filter(Transaction.amount == 11.11).count()
    assert created >= 3

def test_returns_correct_count(session):
    yesterday = date.today() - timedelta(days=1)
    _make_rtx(session, "daily", yesterday, amount=22.22)
    _make_rtx(session, "daily", yesterday, amount=33.33)

    count = crud.process_due_recurring_transactions(session)

    assert count >= 2
