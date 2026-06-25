import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import crud
import schemas
import pytest
from datetime import date

DATE_JAN = date(2026, 1, 1)
DATE_FEB = date(2026, 2, 1)
DATE_MAR = date(2026, 3, 1)
DATE_APR = date(2026, 4, 1)


### NO FILTERS ###

def test_no_filters_includes_created_transaction(session):
    account = crud.create_account(schemas.AccountCreate(name="FAll Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FAll Category"), session)
    tx = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session)
    assert any(t.id == tx.id for t in results)


### SINGLE FILTERS ###

def test_filter_by_account_includes_match(session):
    account = crud.create_account(schemas.AccountCreate(name="FA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FA Category"), session)
    tx = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id)
    assert any(t.id == tx.id for t in results)

def test_filter_by_account_excludes_other_accounts(session):
    account_a = crud.create_account(schemas.AccountCreate(name="FAxcl Account A"), session)
    account_b = crud.create_account(schemas.AccountCreate(name="FAxcl Account B"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FAxcl Category"), session)
    tx_a = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account_a.id, category_id=category.id, type="expense"),
        session,
    )
    tx_b = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_JAN, account_id=account_b.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account_a.id)
    ids = [t.id for t in results]
    assert tx_a.id in ids
    assert tx_b.id not in ids

def test_filter_by_category_includes_match(session):
    account = crud.create_account(schemas.AccountCreate(name="FC Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FC Category"), session)
    tx = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, category_id=category.id)
    assert any(t.id == tx.id for t in results)

def test_filter_by_category_excludes_other_categories(session):
    account = crud.create_account(schemas.AccountCreate(name="FCxcl Account"), session)
    cat_a = crud.create_category(schemas.CategoryCreate(name="FCxcl Category A"), session)
    cat_b = crud.create_category(schemas.CategoryCreate(name="FCxcl Category B"), session)
    tx_a = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=cat_a.id, type="expense"),
        session,
    )
    tx_b = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_JAN, account_id=account.id, category_id=cat_b.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, category_id=cat_a.id)
    ids = [t.id for t in results]
    assert tx_a.id in ids
    assert tx_b.id not in ids

def test_filter_by_start_date_includes_on_and_after(session):
    account = crud.create_account(schemas.AccountCreate(name="FSD Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FSD Category"), session)
    tx_before = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_on = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_after = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_MAR, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, start_date=DATE_FEB)
    ids = [t.id for t in results]
    assert tx_on.id in ids
    assert tx_after.id in ids
    assert tx_before.id not in ids

def test_filter_by_end_date_includes_on_and_before(session):
    account = crud.create_account(schemas.AccountCreate(name="FED Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FED Category"), session)
    tx_before = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_on = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_after = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_MAR, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, end_date=DATE_FEB)
    ids = [t.id for t in results]
    assert tx_before.id in ids
    assert tx_on.id in ids
    assert tx_after.id not in ids

def test_filter_by_date_range(session):
    account = crud.create_account(schemas.AccountCreate(name="FDR Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FDR Category"), session)
    tx_jan = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_feb = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_apr = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_APR, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, start_date=DATE_FEB, end_date=DATE_MAR)
    ids = [t.id for t in results]
    assert tx_feb.id in ids
    assert tx_jan.id not in ids
    assert tx_apr.id not in ids

def test_filter_exact_date(session):
    account = crud.create_account(schemas.AccountCreate(name="FExact Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FExact Category"), session)
    tx_match = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_other = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_MAR, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, start_date=DATE_FEB, end_date=DATE_FEB)
    ids = [t.id for t in results]
    assert tx_match.id in ids
    assert tx_other.id not in ids


### COMBINATIONS OF FILTERS ###

def test_filter_account_and_category(session):
    account_a = crud.create_account(schemas.AccountCreate(name="FAC Account A"), session)
    account_b = crud.create_account(schemas.AccountCreate(name="FAC Account B"), session)
    cat_a = crud.create_category(schemas.CategoryCreate(name="FAC Category A"), session)
    cat_b = crud.create_category(schemas.CategoryCreate(name="FAC Category B"), session)
    tx_match = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account_a.id, category_id=cat_a.id, type="expense"),
        session,
    )
    tx_wrong_account = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_JAN, account_id=account_b.id, category_id=cat_a.id, type="expense"),
        session,
    )
    tx_wrong_category = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_JAN, account_id=account_a.id, category_id=cat_b.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account_a.id, category_id=cat_a.id)
    ids = [t.id for t in results]
    assert tx_match.id in ids
    assert tx_wrong_account.id not in ids
    assert tx_wrong_category.id not in ids

def test_filter_account_and_date_range(session):
    account_a = crud.create_account(schemas.AccountCreate(name="FADR Account A"), session)
    account_b = crud.create_account(schemas.AccountCreate(name="FADR Account B"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FADR Category"), session)
    tx_match = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_FEB, account_id=account_a.id, category_id=category.id, type="expense"),
        session,
    )
    tx_wrong_account = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_FEB, account_id=account_b.id, category_id=category.id, type="expense"),
        session,
    )
    tx_wrong_date = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_APR, account_id=account_a.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account_a.id, start_date=DATE_JAN, end_date=DATE_MAR)
    ids = [t.id for t in results]
    assert tx_match.id in ids
    assert tx_wrong_account.id not in ids
    assert tx_wrong_date.id not in ids

def test_filter_category_and_date_range(session):
    account = crud.create_account(schemas.AccountCreate(name="FCDR Account"), session)
    cat_a = crud.create_category(schemas.CategoryCreate(name="FCDR Category A"), session)
    cat_b = crud.create_category(schemas.CategoryCreate(name="FCDR Category B"), session)
    tx_match = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_FEB, account_id=account.id, category_id=cat_a.id, type="expense"),
        session,
    )
    tx_wrong_category = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_FEB, account_id=account.id, category_id=cat_b.id, type="expense"),
        session,
    )
    tx_wrong_date = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_APR, account_id=account.id, category_id=cat_a.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, category_id=cat_a.id, start_date=DATE_JAN, end_date=DATE_MAR)
    ids = [t.id for t in results]
    assert tx_match.id in ids
    assert tx_wrong_category.id not in ids
    assert tx_wrong_date.id not in ids

def test_all_filters_combined(session):
    account_a = crud.create_account(schemas.AccountCreate(name="FALL Account A"), session)
    account_b = crud.create_account(schemas.AccountCreate(name="FALL Account B"), session)
    cat_a = crud.create_category(schemas.CategoryCreate(name="FALL Category A"), session)
    cat_b = crud.create_category(schemas.CategoryCreate(name="FALL Category B"), session)
    tx_match = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_FEB, account_id=account_a.id, category_id=cat_a.id, type="expense"),
        session,
    )
    tx_wrong_account = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_FEB, account_id=account_b.id, category_id=cat_a.id, type="expense"),
        session,
    )
    tx_wrong_category = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_FEB, account_id=account_a.id, category_id=cat_b.id, type="expense"),
        session,
    )
    tx_wrong_date = crud.create_transaction(
        schemas.TransactionCreate(amount=40.0, date=DATE_APR, account_id=account_a.id, category_id=cat_a.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(
        session, account_id=account_a.id, category_id=cat_a.id, start_date=DATE_JAN, end_date=DATE_MAR
    )
    ids = [t.id for t in results]
    assert tx_match.id in ids
    assert tx_wrong_account.id not in ids
    assert tx_wrong_category.id not in ids
    assert tx_wrong_date.id not in ids


# --- empty results ---

def test_nonexistent_account_returns_empty(session):
    results = crud.read_transactions_filtered(session, account_id=99999)
    assert results == []

def test_nonexistent_category_returns_empty(session):
    results = crud.read_transactions_filtered(session, category_id=99999)
    assert results == []

def test_start_date_after_all_transactions_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="FSDA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FSDA Category"), session)
    crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, start_date=date(2099, 1, 1))
    assert results == []

def test_end_date_before_all_transactions_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="FEDBA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FEDBA Category"), session)
    crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_MAR, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, end_date=date(2000, 1, 1))
    assert results == []

def test_impossible_date_range_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="FImp Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FImp Category"), session)
    crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, start_date=DATE_MAR, end_date=DATE_JAN)
    assert results == []


# --- ordering ---

def test_results_ordered_by_date_desc(session):
    account = crud.create_account(schemas.AccountCreate(name="FORD Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FORD Category"), session)
    tx_feb = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_jan = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_mar = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_MAR, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id)
    ids = [t.id for t in results]
    assert ids.index(tx_mar.id) < ids.index(tx_feb.id) < ids.index(tx_jan.id)

def test_same_date_ordered_by_id_desc(session):
    account = crud.create_account(schemas.AccountCreate(name="FSDO Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FSDO Category"), session)
    tx_first = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_second = crud.create_transaction(
        schemas.TransactionCreate(amount=20.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_third = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id)
    ids = [t.id for t in results]
    assert ids.index(tx_third.id) < ids.index(tx_second.id) < ids.index(tx_first.id)


# --- pagination ---

def test_limit_returns_at_most_n_results(session):
    account = crud.create_account(schemas.AccountCreate(name="FLim Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FLim Category"), session)
    for i in range(5):
        crud.create_transaction(
            schemas.TransactionCreate(amount=float(i + 1), date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
            session,
        )
    results = crud.read_transactions_filtered(session, account_id=account.id, limit=3)
    assert len(results) == 3

def test_offset_skips_first_n_results(session):
    account = crud.create_account(schemas.AccountCreate(name="FOff Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FOff Category"), session)
    txs = [
        crud.create_transaction(
            schemas.TransactionCreate(amount=float(i + 1), date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
            session,
        )
        for i in range(4)
    ]
    all_results = crud.read_transactions_filtered(session, account_id=account.id)
    offset_results = crud.read_transactions_filtered(session, account_id=account.id, offset=2)
    assert offset_results == all_results[2:]

def test_limit_and_offset_returns_correct_page(session):
    account = crud.create_account(schemas.AccountCreate(name="FPag Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FPag Category"), session)
    for i in range(6):
        crud.create_transaction(
            schemas.TransactionCreate(amount=float(i + 1), date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
            session,
        )
    page1 = crud.read_transactions_filtered(session, account_id=account.id, limit=2, offset=0)
    page2 = crud.read_transactions_filtered(session, account_id=account.id, limit=2, offset=2)
    page3 = crud.read_transactions_filtered(session, account_id=account.id, limit=2, offset=4)
    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 2
    all_ids = [t.id for t in page1] + [t.id for t in page2] + [t.id for t in page3]
    assert len(set(all_ids)) == 6

def test_offset_beyond_results_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="FOffE Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FOffE Category"), session)
    crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, offset=999)
    assert results == []

def test_limit_larger_than_results_returns_all(session):
    account = crud.create_account(schemas.AccountCreate(name="FLimL Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FLimL Category"), session)
    for i in range(3):
        crud.create_transaction(
            schemas.TransactionCreate(amount=float(i + 1), date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
            session,
        )
    results = crud.read_transactions_filtered(session, account_id=account.id, limit=100)
    assert len(results) == 3

def test_pagination_with_filters(session):
    account = crud.create_account(schemas.AccountCreate(name="FPagF Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FPagF Category"), session)
    other_category = crud.create_category(schemas.CategoryCreate(name="FPagF Other Category"), session)
    for i in range(4):
        crud.create_transaction(
            schemas.TransactionCreate(amount=float(i + 1), date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
            session,
        )
    crud.create_transaction(
        schemas.TransactionCreate(amount=99.0, date=DATE_JAN, account_id=account.id, category_id=other_category.id, type="expense"),
        session,
    )
    page1 = crud.read_transactions_filtered(session, account_id=account.id, category_id=category.id, limit=2, offset=0)
    page2 = crud.read_transactions_filtered(session, account_id=account.id, category_id=category.id, limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert all(t.category_id == category.id for t in page1 + page2)


# --- amount filters ---

def test_filter_by_type_income(session):
    account = crud.create_account(schemas.AccountCreate(name="FTypInc Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FTypInc Category"), session)
    tx_income = crud.create_transaction(
        schemas.TransactionCreate(amount=50.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="income"),
        session,
    )
    tx_expense = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, tx_type="income")
    ids = [t.id for t in results]
    assert tx_income.id in ids
    assert tx_expense.id not in ids

def test_filter_by_type_expense(session):
    account = crud.create_account(schemas.AccountCreate(name="FTypExp Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FTypExp Category"), session)
    tx_income = crud.create_transaction(
        schemas.TransactionCreate(amount=50.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="income"),
        session,
    )
    tx_expense = crud.create_transaction(
        schemas.TransactionCreate(amount=30.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, tx_type="expense")
    ids = [t.id for t in results]
    assert tx_expense.id in ids
    assert tx_income.id not in ids

def test_filter_type_with_date_range(session):
    account = crud.create_account(schemas.AccountCreate(name="FTypDate Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FTypDate Category"), session)
    tx_match = crud.create_transaction(
        schemas.TransactionCreate(amount=40.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="income"),
        session,
    )
    tx_wrong_type = crud.create_transaction(
        schemas.TransactionCreate(amount=40.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_wrong_date = crud.create_transaction(
        schemas.TransactionCreate(amount=40.0, date=DATE_APR, account_id=account.id, category_id=category.id, type="income"),
        session,
    )
    results = crud.read_transactions_filtered(
        session, account_id=account.id, tx_type="income", start_date=DATE_JAN, end_date=DATE_MAR
    )
    ids = [t.id for t in results]
    assert tx_match.id in ids
    assert tx_wrong_type.id not in ids
    assert tx_wrong_date.id not in ids

def test_filter_min_amount_includes_at_and_above(session):
    account = crud.create_account(schemas.AccountCreate(name="FMinA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FMinA Category"), session)
    tx_low = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_exact = crud.create_transaction(
        schemas.TransactionCreate(amount=50.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_high = crud.create_transaction(
        schemas.TransactionCreate(amount=100.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, min_amount=50.0)
    ids = [t.id for t in results]
    assert tx_exact.id in ids
    assert tx_high.id in ids
    assert tx_low.id not in ids

def test_filter_max_amount_includes_at_and_below(session):
    account = crud.create_account(schemas.AccountCreate(name="FMaxA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FMaxA Category"), session)
    tx_low = crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_exact = crud.create_transaction(
        schemas.TransactionCreate(amount=50.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_high = crud.create_transaction(
        schemas.TransactionCreate(amount=100.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, max_amount=50.0)
    ids = [t.id for t in results]
    assert tx_low.id in ids
    assert tx_exact.id in ids
    assert tx_high.id not in ids

def test_filter_amount_range(session):
    account = crud.create_account(schemas.AccountCreate(name="FAmtR Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FAmtR Category"), session)
    tx_5 = crud.create_transaction(
        schemas.TransactionCreate(amount=5.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_25 = crud.create_transaction(
        schemas.TransactionCreate(amount=25.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_75 = crud.create_transaction(
        schemas.TransactionCreate(amount=75.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_200 = crud.create_transaction(
        schemas.TransactionCreate(amount=200.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, min_amount=20.0, max_amount=100.0)
    ids = [t.id for t in results]
    assert tx_25.id in ids
    assert tx_75.id in ids
    assert tx_5.id not in ids
    assert tx_200.id not in ids

def test_filter_min_amount_above_all_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="FMinE Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FMinE Category"), session)
    crud.create_transaction(
        schemas.TransactionCreate(amount=10.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, min_amount=9999.0)
    assert results == []

def test_filter_max_amount_below_all_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="FMaxE Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FMaxE Category"), session)
    crud.create_transaction(
        schemas.TransactionCreate(amount=100.0, date=DATE_JAN, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(session, account_id=account.id, max_amount=0.01)
    assert results == []

def test_filter_amount_combined_with_date(session):
    account = crud.create_account(schemas.AccountCreate(name="FAmtD Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="FAmtD Category"), session)
    tx_match = crud.create_transaction(
        schemas.TransactionCreate(amount=50.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_wrong_amount = crud.create_transaction(
        schemas.TransactionCreate(amount=5.0, date=DATE_FEB, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    tx_wrong_date = crud.create_transaction(
        schemas.TransactionCreate(amount=50.0, date=DATE_APR, account_id=account.id, category_id=category.id, type="expense"),
        session,
    )
    results = crud.read_transactions_filtered(
        session, account_id=account.id, min_amount=20.0, start_date=DATE_JAN, end_date=DATE_MAR
    )
    ids = [t.id for t in results]
    assert tx_match.id in ids
    assert tx_wrong_amount.id not in ids
    assert tx_wrong_date.id not in ids
