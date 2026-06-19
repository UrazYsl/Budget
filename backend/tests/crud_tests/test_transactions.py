import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import crud
import schemas
import pytest
from datetime import date
from models import Transaction

def test_read_transactions_empty(session):
    transactions = crud.read_transactions(session)
    assert len(transactions) == 0

def test_read_transactions_seeded(session):
    account = crud.create_account(schemas.AccountCreate(name="Seeded Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Seeded Category"), session)
    tx = crud.create_transaction(
        schemas.TransactionCreate(
            amount=200.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    transactions = crud.read_transactions(session)
    assert any(t.id == tx.id for t in transactions)

def test_create_transaction(session):
    account = crud.create_account(schemas.AccountCreate(name="Test Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Test Category"), session)
    transaction = crud.create_transaction(
        schemas.TransactionCreate(
            amount=100.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    assert transaction.amount == 100.0
    assert transaction.account_id == account.id
    assert transaction.category_id == category.id

def test_create_transaction_invalid_account(session):
    category = crud.create_category(schemas.CategoryCreate(name="Invalid Account Category"), session)
    with pytest.raises(Exception):
        crud.create_transaction(
            schemas.TransactionCreate(
                amount=50.0,
                date=date.today(),
                account_id=9999,
                category_id=category.id
            ),
            session
        )
    session.rollback()

def test_create_transaction_invalid_category(session):
    account = crud.create_account(schemas.AccountCreate(name="Invalid Category Account"), session)
    with pytest.raises(Exception):
        crud.create_transaction(
            schemas.TransactionCreate(
                amount=75.0,
                date=date.today(),
                account_id=account.id,
                category_id=9999
            ),
            session
        )
    session.rollback()

def test_create_transaction_negative_amount(session):
    account = crud.create_account(schemas.AccountCreate(name="Negative Amount Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Negative Amount Category"), session)
    with pytest.raises(Exception):
        crud.create_transaction(
            schemas.TransactionCreate(
                amount=-50.0,
                date=date.today(),
                account_id=account.id,
                category_id=category.id
            ),
            session
        )

def test_create_transaction_zero_amount(session):
    account = crud.create_account(schemas.AccountCreate(name="Zero Amount Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Zero Amount Category"), session)
    with pytest.raises(Exception):
        crud.create_transaction(
            schemas.TransactionCreate(
                amount=0.0,
                date=date.today(),
                account_id=account.id,
                category_id=category.id
            ),
            session
        )

def test_update_existing_transaction(session):
    account = crud.create_account(schemas.AccountCreate(name="Update Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Update Category"), session)
    transaction = crud.create_transaction(
        schemas.TransactionCreate(
            amount=150.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    result = crud.update_transaction(
        transaction.id,
        schemas.TransactionCreate(
            amount=175.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    assert result == 1
    updated_transaction = session.query(Transaction).filter(Transaction.id == transaction.id).first()
    assert updated_transaction.amount == 175.0

def test_update_nonexistent_transaction(session):
    account = crud.create_account(schemas.AccountCreate(name="Nonexistent Tx Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Nonexistent Tx Category"), session)
    result = crud.update_transaction(
        9999,
        schemas.TransactionCreate(
            amount=200.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    assert result == 0

def test_delete_existing_transaction(session):
    account = crud.create_account(schemas.AccountCreate(name="Delete Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Delete Category"), session)
    transaction = crud.create_transaction(
        schemas.TransactionCreate(
            amount=125.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    transaction_id = transaction.id
    result = crud.delete_transaction(transaction_id, session)
    session.expire_all()
    assert result == 1
    deleted_transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
    assert deleted_transaction is None

def test_delete_nonexistent_transaction(session):
    result = crud.delete_transaction(9999, session)
    assert result == 0

def test_delete_category_sets_misc(session):
    account = crud.create_account(schemas.AccountCreate(name="Account For Category Deletion"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Category To Delete With Transaction"), session)
    transaction = crud.create_transaction(
        schemas.TransactionCreate(
            amount=80.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    category_id = category.id
    transaction_id = transaction.id
    crud.delete_category(category_id, session)
    session.expire_all()
    misc = session.query(crud.Category).filter(crud.Category.name == "Misc").first()
    remaining = session.query(Transaction).filter(Transaction.id == transaction_id).first()
    assert remaining is not None
    assert remaining.category_id == misc.id

def test_delete_account_cascades_transactions(session):
    account = crud.create_account(schemas.AccountCreate(name="Account To Delete With Transaction"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Category For Account Deletion"), session)
    transaction = crud.create_transaction(
        schemas.TransactionCreate(
            amount=90.0,
            date=date.today(),
            account_id=account.id,
            category_id=category.id
        ),
        session
    )
    account_id = account.id
    transaction_id = transaction.id
    result = crud.delete_account(account_id, session)
    session.expire_all()
    assert result == 1
    deleted_account = session.query(crud.Account).filter(crud.Account.id == account_id).first()
    assert deleted_account is None
    deleted_transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
    assert deleted_transaction is None
