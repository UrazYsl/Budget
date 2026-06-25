import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import uuid
import crud
import schemas
from datetime import date


def _make_tx(session):
    suffix = uuid.uuid4().hex[:8]
    account = crud.create_account(schemas.AccountCreate(name=f"Receipt Account {suffix}"), session)
    category = crud.create_category(schemas.CategoryCreate(name=f"Receipt Category {suffix}"), session)
    return crud.create_transaction(
        schemas.TransactionCreate(
            date=date.today(),
            amount=10.0,
            type="expense",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )


def test_get_transaction_returns_correct(session):
    tx = _make_tx(session)
    result = crud.get_transaction(session, tx.id)
    assert result is not None
    assert result.id == tx.id
    assert result.amount == tx.amount

def test_get_transaction_nonexistent_returns_none(session):
    result = crud.get_transaction(session, 999999)
    assert result is None

def test_receipt_path_defaults_to_none(session):
    tx = _make_tx(session)
    assert tx.receipt_path is None

def test_set_receipt_path_returns_1(session):
    tx = _make_tx(session)
    result = crud.set_receipt_path(session, tx.id, "42.jpg")
    assert result == 1

def test_set_receipt_path_stores_value(session):
    tx = _make_tx(session)
    crud.set_receipt_path(session, tx.id, "99.png")
    session.expire_all()
    updated = crud.get_transaction(session, tx.id)
    assert updated.receipt_path == "99.png"

def test_set_receipt_path_nonexistent_returns_0(session):
    result = crud.set_receipt_path(session, 999999, "whatever.jpg")
    assert result == 0

def test_set_receipt_path_can_clear_to_none(session):
    tx = _make_tx(session)
    crud.set_receipt_path(session, tx.id, "temp.jpg")
    crud.set_receipt_path(session, tx.id, None)
    session.expire_all()
    updated = crud.get_transaction(session, tx.id)
    assert updated.receipt_path is None

def test_update_transaction_does_not_clear_receipt_path(session):
    account = crud.create_account(schemas.AccountCreate(name="Receipt Persist Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Receipt Persist Category"), session)
    tx = crud.create_transaction(
        schemas.TransactionCreate(
            date=date.today(),
            amount=50.0,
            type="expense",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    crud.set_receipt_path(session, tx.id, "keep.jpg")
    crud.update_transaction(
        tx.id,
        schemas.TransactionCreate(
            date=date.today(),
            amount=75.0,
            type="income",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    )
    session.expire_all()
    updated = crud.get_transaction(session, tx.id)
    assert updated.amount == 75.0
    assert updated.receipt_path == "keep.jpg"
