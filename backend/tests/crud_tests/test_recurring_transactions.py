import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import crud
import schemas
import pytest
from datetime import date
from models import RecurringTransaction

def test_read_recurring_transactions_empty(session):
    recurring_transactions = crud.read_recurring_transactions(session)
    assert len(recurring_transactions) == 0

def test_create_recurring_transaction(session):
    account = crud.create_account(schemas.AccountCreate(name="Test Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Test Category"), session)
    rtx = crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=100.0,
            next_run_date=date.today(),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    assert rtx.amount == 100.0
    assert rtx.account_id == account.id
    assert rtx.category_id == category.id
    assert rtx.recurring_interval == "monthly"

def test_read_recurring_transactions(session):
    account = crud.create_account(schemas.AccountCreate(name="Read Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Read Category"), session)
    rtx = crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=200.0,
            next_run_date=date.today(),
            recurring_interval="weekly",
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    all_rtx = crud.read_recurring_transactions(session)
    assert any(r.id == rtx.id for r in all_rtx)

def test_create_recurring_transaction_invalid_account(session):
    category = crud.create_category(schemas.CategoryCreate(name="Invalid Account Category"), session)
    with pytest.raises(Exception):
        crud.create_recurring_transaction(
            schemas.RecurringTransactionCreate(
                amount=50.0,
                next_run_date=date.today(),
                recurring_interval="monthly",
                account_id=9999,
                category_id=category.id
            ),
            session
        )
    session.rollback()

def test_create_recurring_transaction_invalid_category(session):
    account = crud.create_account(schemas.AccountCreate(name="Invalid Category Account"), session)
    with pytest.raises(Exception):
        crud.create_recurring_transaction(
            schemas.RecurringTransactionCreate(
                amount=50.0,
                next_run_date=date.today(),
                recurring_interval="monthly",
                account_id=account.id,
                category_id=9999
            ),
            session
        )
    session.rollback()

def test_create_recurring_transaction_invalid_interval(session):
    account = crud.create_account(schemas.AccountCreate(name="Invalid Interval Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Invalid Interval Category"), session)
    with pytest.raises(Exception):
        crud.create_recurring_transaction(
            schemas.RecurringTransactionCreate(
                amount=50.0,
                next_run_date=date.today(),
                recurring_interval="invalid",
                account_id=account.id,
                category_id=category.id
            ),
            session
        )

def test_create_recurring_transaction_negative_amount(session):
    account = crud.create_account(schemas.AccountCreate(name="Negative Amount Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Negative Amount Category"), session)
    with pytest.raises(Exception):
        crud.create_recurring_transaction(
            schemas.RecurringTransactionCreate(
                amount=-50.0,
                next_run_date=date.today(),
                recurring_interval="monthly",
                account_id=account.id,
                category_id=category.id
            ),
            session
        )

def test_create_recurring_transaction_zero_amount(session):
    account = crud.create_account(schemas.AccountCreate(name="Zero Amount Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Zero Amount Category"), session)
    with pytest.raises(Exception):
        crud.create_recurring_transaction(
            schemas.RecurringTransactionCreate(
                amount=0.0,
                next_run_date=date.today(),
                recurring_interval="monthly",
                account_id=account.id,
                category_id=category.id
            ),
            session
        )

def test_delete_recurring_transaction(session):
    account = crud.create_account(schemas.AccountCreate(name="Delete Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Delete Category"), session)
    rtx = crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=150.0,
            next_run_date=date.today(),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    rtx_id = rtx.id
    result = crud.delete_recurring_transaction(rtx_id, session)
    session.expire_all()
    assert result == 1
    deleted = session.query(RecurringTransaction).filter(RecurringTransaction.id == rtx_id).first()
    assert deleted is None

def test_delete_nonexistent_recurring_transaction(session):
    result = crud.delete_recurring_transaction(9999, session)
    assert result == 0

def test_delete_account_cascades_recurring_transactions(session):
    account = crud.create_account(schemas.AccountCreate(name="Cascade Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Cascade Category"), session)
    rtx = crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=100.0,
            next_run_date=date.today(),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    rtx_id = rtx.id
    account_id = account.id
    crud.delete_account(account_id, session)
    session.expire_all()
    deleted = session.query(RecurringTransaction).filter(RecurringTransaction.id == rtx_id).first()
    assert deleted is None

def test_delete_category_cascades_recurring_transactions(session):
    account = crud.create_account(schemas.AccountCreate(name="Category Cascade Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Category Cascade Category"), session)
    rtx = crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=100.0,
            next_run_date=date.today(),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    rtx_id = rtx.id
    category_id = category.id
    crud.delete_category(category_id, session)
    session.expire_all()
    deleted = session.query(RecurringTransaction).filter(RecurringTransaction.id == rtx_id).first()
    assert deleted is None


### UPDATE ###

def _make_rtx(name_suffix, session, amount=50.0, interval="monthly", next_run_date=None):
    account = crud.create_account(schemas.AccountCreate(name=f"Upd Account {name_suffix}"), session)
    category = crud.create_category(schemas.CategoryCreate(name=f"Upd Category {name_suffix}"), session)
    rtx = crud.create_recurring_transaction(
        schemas.RecurringTransactionCreate(
            amount=amount,
            next_run_date=next_run_date or date(2026, 1, 1),
            recurring_interval=interval,
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    return rtx, account, category

def test_update_recurring_transaction_returns_1(session):
    rtx, account, category = _make_rtx("Ret1", session)
    result = crud.update_recurring_transaction(
        rtx.id,
        schemas.RecurringTransactionCreate(
            amount=99.0,
            next_run_date=date(2026, 6, 1),
            recurring_interval="weekly",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    assert result == 1

def test_update_recurring_transaction_nonexistent_returns_0(session):
    account = crud.create_account(schemas.AccountCreate(name="Upd Account NonEx"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Upd Category NonEx"), session)
    result = crud.update_recurring_transaction(
        9999,
        schemas.RecurringTransactionCreate(
            amount=50.0,
            next_run_date=date(2026, 1, 1),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    assert result == 0

def test_update_recurring_transaction_updates_amount(session):
    rtx, account, category = _make_rtx("Amt", session, amount=50.0)
    crud.update_recurring_transaction(
        rtx.id,
        schemas.RecurringTransactionCreate(
            amount=200.0,
            next_run_date=date(2026, 1, 1),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    session.expire_all()
    updated = session.get(RecurringTransaction, rtx.id)
    assert updated.amount == 200.0

def test_update_recurring_transaction_updates_interval(session):
    rtx, account, category = _make_rtx("Interval", session, interval="monthly")
    crud.update_recurring_transaction(
        rtx.id,
        schemas.RecurringTransactionCreate(
            amount=50.0,
            next_run_date=date(2026, 1, 1),
            recurring_interval="yearly",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    session.expire_all()
    updated = session.get(RecurringTransaction, rtx.id)
    assert updated.recurring_interval == "yearly"

def test_update_recurring_transaction_updates_next_run_date(session):
    rtx, account, category = _make_rtx("Date", session, next_run_date=date(2026, 1, 1))
    crud.update_recurring_transaction(
        rtx.id,
        schemas.RecurringTransactionCreate(
            amount=50.0,
            next_run_date=date(2026, 12, 31),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    session.expire_all()
    updated = session.get(RecurringTransaction, rtx.id)
    assert updated.next_run_date == date(2026, 12, 31)

def test_update_recurring_transaction_updates_account(session):
    rtx, old_account, category = _make_rtx("AccSwap", session)
    new_account = crud.create_account(schemas.AccountCreate(name="Upd Account AccSwap New"), session)
    crud.update_recurring_transaction(
        rtx.id,
        schemas.RecurringTransactionCreate(
            amount=50.0,
            next_run_date=date(2026, 1, 1),
            recurring_interval="monthly",
            account_id=new_account.id,
            category_id=category.id,
        ),
        session,
    )
    session.expire_all()
    updated = session.get(RecurringTransaction, rtx.id)
    assert updated.account_id == new_account.id

def test_update_recurring_transaction_updates_category(session):
    rtx, account, old_category = _make_rtx("CatSwap", session)
    new_category = crud.create_category(schemas.CategoryCreate(name="Upd Category CatSwap New"), session)
    crud.update_recurring_transaction(
        rtx.id,
        schemas.RecurringTransactionCreate(
            amount=50.0,
            next_run_date=date(2026, 1, 1),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=new_category.id,
        ),
        session,
    )
    session.expire_all()
    updated = session.get(RecurringTransaction, rtx.id)
    assert updated.category_id == new_category.id

def test_update_recurring_transaction_all_fields(session):
    rtx, _, _ = _make_rtx("AllFields", session, amount=10.0, interval="daily", next_run_date=date(2026, 1, 1))
    new_account = crud.create_account(schemas.AccountCreate(name="Upd Account AllFields New"), session)
    new_category = crud.create_category(schemas.CategoryCreate(name="Upd Category AllFields New"), session)
    crud.update_recurring_transaction(
        rtx.id,
        schemas.RecurringTransactionCreate(
            amount=999.0,
            next_run_date=date(2027, 6, 15),
            recurring_interval="weekly",
            account_id=new_account.id,
            category_id=new_category.id,
        ),
        session,
    )
    session.expire_all()
    updated = session.get(RecurringTransaction, rtx.id)
    assert updated.amount == 999.0
    assert updated.recurring_interval == "weekly"
    assert updated.next_run_date == date(2027, 6, 15)
    assert updated.account_id == new_account.id
    assert updated.category_id == new_category.id

def test_update_recurring_transaction_does_not_affect_others(session):
    rtx_a, account, category = _make_rtx("Isolation A", session, amount=10.0)
    rtx_b, _, _ = _make_rtx("Isolation B", session, amount=20.0)
    crud.update_recurring_transaction(
        rtx_a.id,
        schemas.RecurringTransactionCreate(
            amount=999.0,
            next_run_date=date(2026, 1, 1),
            recurring_interval="monthly",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    session.expire_all()
    unchanged = session.get(RecurringTransaction, rtx_b.id)
    assert unchanged.amount == 20.0

def test_update_recurring_transaction_invalid_account_raises(session):
    rtx, _, category = _make_rtx("InvAcc", session)
    with pytest.raises(Exception):
        crud.update_recurring_transaction(
            rtx.id,
            schemas.RecurringTransactionCreate(
                amount=50.0,
                next_run_date=date(2026, 1, 1),
                recurring_interval="monthly",
                account_id=9999,
                category_id=category.id,
            ),
            session,
        )
    session.rollback()

def test_update_recurring_transaction_invalid_category_raises(session):
    rtx, account, _ = _make_rtx("InvCat", session)
    with pytest.raises(Exception):
        crud.update_recurring_transaction(
            rtx.id,
            schemas.RecurringTransactionCreate(
                amount=50.0,
                next_run_date=date(2026, 1, 1),
                recurring_interval="monthly",
                account_id=account.id,
                category_id=9999,
            ),
            session,
        )
    session.rollback()
