import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import crud
import schemas
import pytest
from datetime import date
from models import RecurringTransaction

# get_test_session always seeds 4 categories, so we check for exactly 4 instead of empty
def test_read_categories_seeded(session):
    categories = crud.read_categories(session)
    assert len(categories) == 4

def test_create_category(session):
    category = crud.create_category(schemas.CategoryCreate(name="Test Category"), session)
    assert category.name == "Test Category"
    assert category.id is not None

def test_create_duplicate_category(session):
    crud.create_category(schemas.CategoryCreate(name="Duplicate Category"), session)
    with pytest.raises(Exception):
        crud.create_category(schemas.CategoryCreate(name="Duplicate Category"), session)
    session.rollback()

def test_read_categories(session):
    category = crud.create_category(schemas.CategoryCreate(name="Read Test"), session)
    categories = crud.read_categories(session)
    assert any(c.id == category.id for c in categories)

def test_update_existing_category(session):
    category = crud.create_category(schemas.CategoryCreate(name="Old Name"), session)
    result = crud.update_category(category.id, "New Name", session)
    assert result == 1
    updated_category = session.query(crud.Category).filter(crud.Category.id == category.id).first()
    assert updated_category.name == "New Name"
    old_category = session.query(crud.Category).filter(crud.Category.name == "Old Name").first()
    assert old_category is None

def test_update_nonexistent_category(session):
    result = crud.update_category(9999, "Should Not Exist", session)
    assert result == 0

def test_delete_existing_category(session):
    category = crud.create_category(schemas.CategoryCreate(name="To Be Deleted"), session)
    category_id = category.id
    result = crud.delete_category(category_id, session)
    session.expire_all()
    assert result == 1
    deleted_category = session.query(crud.Category).filter(crud.Category.id == category_id).first()
    assert deleted_category is None

def test_delete_nonexistent_category(session):
    result = crud.delete_category(9999, session)
    assert result == 0

def test_delete_category_with_recurring_transaction(session):
    category = crud.create_category(schemas.CategoryCreate(name="Category With Recurring"), session)
    account = crud.create_account(schemas.AccountCreate(name="Account For Recurring"), session)
    category_id = category.id
    recurring_transaction = RecurringTransaction(
        amount=100,
        type="expense",
        recurring_interval="monthly",
        next_run_date=date(2024, 1, 1),
        account_id=account.id,
        category_id=category_id
    )
    session.add(recurring_transaction)
    session.commit()
    result = crud.delete_category(category_id, session)
    session.expire_all()
    assert result == 1
    deleted_category = session.query(crud.Category).filter(crud.Category.id == category_id).first()
    assert deleted_category is None
    deleted_rtx = session.query(RecurringTransaction).filter(RecurringTransaction.category_id == category_id).first()
    assert deleted_rtx is None
