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
