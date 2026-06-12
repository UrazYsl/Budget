import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from typing import Type
import pytest
from tester_db_setup import get_test_session
from sqlalchemy.orm import Session, sessionmaker
import crud
import schemas
session = get_test_session()

def test_create_account():
    account = crud.create_account(schemas.AccountCreate(name="Test Account"), session)
    assert account.name == "Test Account"

def test_read_accounts():
    account = crud.create_account(schemas.AccountCreate(name="Read Test"), session)
    accounts = crud.read_accounts(session)
    assert any(a.id == account.id for a in accounts)

def test_update_account():
    account = crud.create_account(schemas.AccountCreate(name="Old Name"), session)
    result = crud.update_account(account.id, "New Name", session)
    assert result == 1
    updated_account = session.query(crud.Account).filter(crud.Account.id == account.id).first()
    assert updated_account.name == "New Name"

def test_delete_account():
    account = crud.create_account(schemas.AccountCreate(name="To Be Deleted"), session)
    result = crud.delete_account(account.id, session)
    assert result == 1
    deleted_account = session.query(crud.Account).filter(crud.Account.id == account.id).first()
    assert deleted_account is None
