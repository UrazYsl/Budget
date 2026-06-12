import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from typing import Type
import pytest
from tester_db_setup import get_test_session
from sqlalchemy.orm import Session, sessionmaker
import crud
import schemas
from datetime import date
from models import RecurringTransaction

session = get_test_session()

def test_read_accounts_empty():
    accounts = crud.read_accounts(session)
    assert accounts == []

def test_create_account():
    account = crud.create_account(schemas.AccountCreate(name="Test Account"), session)
    assert account.name == "Test Account"
    assert account.id is not None

def test_create_duplicate_account():
    crud.create_account(schemas.AccountCreate(name="Duplicate Account"), session)
    with pytest.raises(Exception):
        crud.create_account(schemas.AccountCreate(name="Duplicate Account"), session)
    session.rollback()

def test_read_accounts():
    account = crud.create_account(schemas.AccountCreate(name="Read Test"), session)
    accounts = crud.read_accounts(session)
    assert any(a.id == account.id for a in accounts)

def test_update_existing_account():
    account = crud.create_account(schemas.AccountCreate(name="Old Name"), session)
    result = crud.update_account(account.id, "New Name", session)
    assert result == 1
    updated_account = session.query(crud.Account).filter(crud.Account.id == account.id).first()
    assert updated_account.name == "New Name"
    old_account = session.query(crud.Account).filter(crud.Account.name == "Old Name").first()
    assert old_account is None

def test_update_nonexistent_account():
    result = crud.update_account(9999, "Should Not Exist", session)
    assert result == 0

def test_delete_existing_account():
    account = crud.create_account(schemas.AccountCreate(name="To Be Deleted"), session)
    result = crud.delete_account(account.id, session)
    assert result == 1
    deleted_account = session.query(crud.Account).filter(crud.Account.id == account.id).first()
    assert deleted_account is None

def test_delete_nonexistent_account():
    result = crud.delete_account(9999, session)
    assert result == 0

def test_delete_account_with_recurring_transactions():
    account = crud.create_account(schemas.AccountCreate(name="Account With Recurring"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Recurring Category"), session)
    recurring_transaction = RecurringTransaction(
        amount=100,
        recurring_interval="monthly",
        next_run_date=date(2024, 1, 1),
        account_id=account.id,
        category_id=category.id
    )
    session.add(recurring_transaction)
    session.commit()
    result = crud.delete_account(account.id, session)
    assert result == 1
    deleted_account = session.query(crud.Account).filter(crud.Account.id == account.id).first()
    assert deleted_account is None
