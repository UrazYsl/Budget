import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import crud
import schemas
from datetime import date, timedelta


def _make_rtx(session, days_from_today, amount=10.0):
    account = crud.create_account(schemas.AccountCreate(name=f"UpAcc d{days_from_today} a{amount}"), session)
    category = crud.create_category(schemas.CategoryCreate(name=f"UpCat d{days_from_today} a{amount}"), session)
    return crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=amount,
            type="expense",
            recurring_interval="monthly",
            next_run_date=date.today() + timedelta(days=days_from_today),
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )


def test_upcoming_includes_due_today(session):
    rtx = _make_rtx(session, 0)
    results = crud.get_upcoming_recurring(session)
    assert any(r.id == rtx.id for r in results)

def test_upcoming_includes_within_window(session):
    rtx = _make_rtx(session, 5, amount=11.0)
    results = crud.get_upcoming_recurring(session)
    assert any(r.id == rtx.id for r in results)

def test_upcoming_includes_on_last_day_of_window(session):
    rtx = _make_rtx(session, 7, amount=12.0)
    results = crud.get_upcoming_recurring(session)
    assert any(r.id == rtx.id for r in results)

def test_upcoming_excludes_beyond_window(session):
    rtx = _make_rtx(session, 8, amount=13.0)
    results = crud.get_upcoming_recurring(session)
    assert not any(r.id == rtx.id for r in results)

def test_upcoming_excludes_past(session):
    rtx = _make_rtx(session, -1, amount=14.0)
    results = crud.get_upcoming_recurring(session)
    assert not any(r.id == rtx.id for r in results)

def test_upcoming_custom_days_window(session):
    rtx_near = _make_rtx(session, 3, amount=15.0)
    rtx_far = _make_rtx(session, 15, amount=16.0)
    in_7 = crud.get_upcoming_recurring(session, days=7)
    in_30 = crud.get_upcoming_recurring(session, days=30)
    assert any(r.id == rtx_near.id for r in in_7)
    assert not any(r.id == rtx_far.id for r in in_7)
    assert any(r.id == rtx_far.id for r in in_30)

def test_upcoming_ordered_by_date_asc(session):
    rtx_later = _make_rtx(session, 6, amount=17.0)
    rtx_sooner = _make_rtx(session, 2, amount=18.0)
    results = crud.get_upcoming_recurring(session)
    ids = [r.id for r in results]
    assert ids.index(rtx_sooner.id) < ids.index(rtx_later.id)
