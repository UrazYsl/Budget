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

def _rtx(amount, next_run_date, account_id, category_id, interval="monthly"):
    return schemas.RecurringTransactionCreate(
        amount=amount,
        next_run_date=next_run_date,
        recurring_interval=interval,
        account_id=account_id,
        category_id=category_id,
    )


### NO FILTERS ###

def test_rf_no_filters_includes_created(session):
    account = crud.create_account(schemas.AccountCreate(name="RFAll Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFAll Category"), session)
    rtx = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session)
    assert any(r.id == rtx.id for r in results)


### SINGLE FILTERS ###

def test_rf_filter_by_account_includes_match(session):
    account = crud.create_account(schemas.AccountCreate(name="RFA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFA Category"), session)
    rtx = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id)
    assert any(r.id == rtx.id for r in results)

def test_rf_filter_by_account_excludes_others(session):
    account_a = crud.create_account(schemas.AccountCreate(name="RFAxcl Account A"), session)
    account_b = crud.create_account(schemas.AccountCreate(name="RFAxcl Account B"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFAxcl Category"), session)
    rtx_a = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account_a.id, category.id), session)
    rtx_b = crud.create_recurring_transaction(_rtx(20.0, DATE_JAN, account_b.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account_a.id)
    ids = [r.id for r in results]
    assert rtx_a.id in ids
    assert rtx_b.id not in ids

def test_rf_filter_by_category_includes_match(session):
    account = crud.create_account(schemas.AccountCreate(name="RFC Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFC Category"), session)
    rtx = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, category_id=category.id)
    assert any(r.id == rtx.id for r in results)

def test_rf_filter_by_category_excludes_others(session):
    account = crud.create_account(schemas.AccountCreate(name="RFCxcl Account"), session)
    cat_a = crud.create_category(schemas.CategoryCreate(name="RFCxcl Category A"), session)
    cat_b = crud.create_category(schemas.CategoryCreate(name="RFCxcl Category B"), session)
    rtx_a = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, cat_a.id), session)
    rtx_b = crud.create_recurring_transaction(_rtx(20.0, DATE_JAN, account.id, cat_b.id), session)
    results = crud.read_recurring_transactions_filtered(session, category_id=cat_a.id)
    ids = [r.id for r in results]
    assert rtx_a.id in ids
    assert rtx_b.id not in ids

def test_rf_filter_by_interval_includes_match(session):
    account = crud.create_account(schemas.AccountCreate(name="RFI Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFI Category"), session)
    rtx = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id, interval="weekly"), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, recurring_interval="weekly")
    assert any(r.id == rtx.id for r in results)

def test_rf_filter_by_interval_excludes_others(session):
    account = crud.create_account(schemas.AccountCreate(name="RFIxcl Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFIxcl Category"), session)
    rtx_weekly = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id, interval="weekly"), session)
    rtx_monthly = crud.create_recurring_transaction(_rtx(20.0, DATE_JAN, account.id, category.id, interval="monthly"), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, recurring_interval="weekly")
    ids = [r.id for r in results]
    assert rtx_weekly.id in ids
    assert rtx_monthly.id not in ids

def test_rf_filter_by_start_date_includes_on_and_after(session):
    account = crud.create_account(schemas.AccountCreate(name="RFSD Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFSD Category"), session)
    rtx_before = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    rtx_on = crud.create_recurring_transaction(_rtx(20.0, DATE_FEB, account.id, category.id), session)
    rtx_after = crud.create_recurring_transaction(_rtx(30.0, DATE_MAR, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, start_date=DATE_FEB)
    ids = [r.id for r in results]
    assert rtx_on.id in ids
    assert rtx_after.id in ids
    assert rtx_before.id not in ids

def test_rf_filter_by_end_date_includes_on_and_before(session):
    account = crud.create_account(schemas.AccountCreate(name="RFED Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFED Category"), session)
    rtx_before = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    rtx_on = crud.create_recurring_transaction(_rtx(20.0, DATE_FEB, account.id, category.id), session)
    rtx_after = crud.create_recurring_transaction(_rtx(30.0, DATE_MAR, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, end_date=DATE_FEB)
    ids = [r.id for r in results]
    assert rtx_before.id in ids
    assert rtx_on.id in ids
    assert rtx_after.id not in ids

def test_rf_filter_by_date_range(session):
    account = crud.create_account(schemas.AccountCreate(name="RFDR Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFDR Category"), session)
    rtx_jan = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    rtx_feb = crud.create_recurring_transaction(_rtx(20.0, DATE_FEB, account.id, category.id), session)
    rtx_apr = crud.create_recurring_transaction(_rtx(30.0, DATE_APR, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, start_date=DATE_FEB, end_date=DATE_MAR)
    ids = [r.id for r in results]
    assert rtx_feb.id in ids
    assert rtx_jan.id not in ids
    assert rtx_apr.id not in ids

def test_rf_filter_exact_date(session):
    account = crud.create_account(schemas.AccountCreate(name="RFExact Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFExact Category"), session)
    rtx_match = crud.create_recurring_transaction(_rtx(10.0, DATE_FEB, account.id, category.id), session)
    rtx_other = crud.create_recurring_transaction(_rtx(20.0, DATE_MAR, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, start_date=DATE_FEB, end_date=DATE_FEB)
    ids = [r.id for r in results]
    assert rtx_match.id in ids
    assert rtx_other.id not in ids


### COMBINATIONS OF FILTERS ###

def test_rf_filter_account_and_interval(session):
    account_a = crud.create_account(schemas.AccountCreate(name="RFAI Account A"), session)
    account_b = crud.create_account(schemas.AccountCreate(name="RFAI Account B"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFAI Category"), session)
    rtx_match = crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account_a.id, category.id, "weekly"), session)
    rtx_wrong_account = crud.create_recurring_transaction(_rtx(20.0, DATE_JAN, account_b.id, category.id, "weekly"), session)
    rtx_wrong_interval = crud.create_recurring_transaction(_rtx(30.0, DATE_JAN, account_a.id, category.id, "monthly"), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account_a.id, recurring_interval="weekly")
    ids = [r.id for r in results]
    assert rtx_match.id in ids
    assert rtx_wrong_account.id not in ids
    assert rtx_wrong_interval.id not in ids

def test_rf_filter_interval_and_date_range(session):
    account = crud.create_account(schemas.AccountCreate(name="RFIDR Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFIDR Category"), session)
    rtx_match = crud.create_recurring_transaction(_rtx(10.0, DATE_FEB, account.id, category.id, "monthly"), session)
    rtx_wrong_interval = crud.create_recurring_transaction(_rtx(20.0, DATE_FEB, account.id, category.id, "yearly"), session)
    rtx_wrong_date = crud.create_recurring_transaction(_rtx(30.0, DATE_APR, account.id, category.id, "monthly"), session)
    results = crud.read_recurring_transactions_filtered(
        session, account_id=account.id, recurring_interval="monthly", start_date=DATE_JAN, end_date=DATE_MAR
    )
    ids = [r.id for r in results]
    assert rtx_match.id in ids
    assert rtx_wrong_interval.id not in ids
    assert rtx_wrong_date.id not in ids

def test_rf_all_filters_combined(session):
    account_a = crud.create_account(schemas.AccountCreate(name="RFALL Account A"), session)
    account_b = crud.create_account(schemas.AccountCreate(name="RFALL Account B"), session)
    cat_a = crud.create_category(schemas.CategoryCreate(name="RFALL Category A"), session)
    cat_b = crud.create_category(schemas.CategoryCreate(name="RFALL Category B"), session)
    rtx_match = crud.create_recurring_transaction(_rtx(10.0, DATE_FEB, account_a.id, cat_a.id, "weekly"), session)
    rtx_wrong_account = crud.create_recurring_transaction(_rtx(20.0, DATE_FEB, account_b.id, cat_a.id, "weekly"), session)
    rtx_wrong_category = crud.create_recurring_transaction(_rtx(30.0, DATE_FEB, account_a.id, cat_b.id, "weekly"), session)
    rtx_wrong_interval = crud.create_recurring_transaction(_rtx(40.0, DATE_FEB, account_a.id, cat_a.id, "daily"), session)
    rtx_wrong_date = crud.create_recurring_transaction(_rtx(50.0, DATE_APR, account_a.id, cat_a.id, "weekly"), session)
    results = crud.read_recurring_transactions_filtered(
        session,
        account_id=account_a.id,
        category_id=cat_a.id,
        recurring_interval="weekly",
        start_date=DATE_JAN,
        end_date=DATE_MAR,
    )
    ids = [r.id for r in results]
    assert rtx_match.id in ids
    assert rtx_wrong_account.id not in ids
    assert rtx_wrong_category.id not in ids
    assert rtx_wrong_interval.id not in ids
    assert rtx_wrong_date.id not in ids


### EMPTY RESULTS ###

def test_rf_nonexistent_account_returns_empty(session):
    results = crud.read_recurring_transactions_filtered(session, account_id=99999)
    assert results == []

def test_rf_nonexistent_category_returns_empty(session):
    results = crud.read_recurring_transactions_filtered(session, category_id=99999)
    assert results == []

def test_rf_unknown_interval_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="RFUnkI Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFUnkI Category"), session)
    crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id, "monthly"), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, recurring_interval="hourly")
    assert results == []

def test_rf_start_date_after_all_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="RFSDA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFSDA Category"), session)
    crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, start_date=date(2099, 1, 1))
    assert results == []

def test_rf_end_date_before_all_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="RFEDBA Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFEDBA Category"), session)
    crud.create_recurring_transaction(_rtx(10.0, DATE_MAR, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, end_date=date(2000, 1, 1))
    assert results == []

def test_rf_impossible_date_range_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="RFImp Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFImp Category"), session)
    crud.create_recurring_transaction(_rtx(10.0, DATE_FEB, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, start_date=DATE_MAR, end_date=DATE_JAN)
    assert results == []


### ORDERING ###

def test_rf_results_ordered_by_next_run_date_asc(session):
    account = crud.create_account(schemas.AccountCreate(name="RFORD Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFORD Category"), session)
    rtx_feb = crud.create_recurring_transaction(_rtx(10.0, DATE_FEB, account.id, category.id), session)
    rtx_jan = crud.create_recurring_transaction(_rtx(20.0, DATE_JAN, account.id, category.id), session)
    rtx_mar = crud.create_recurring_transaction(_rtx(30.0, DATE_MAR, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id)
    ids = [r.id for r in results]
    assert ids.index(rtx_jan.id) < ids.index(rtx_feb.id) < ids.index(rtx_mar.id)

def test_rf_same_date_ordered_by_id_asc(session):
    account = crud.create_account(schemas.AccountCreate(name="RFSDO Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFSDO Category"), session)
    rtx_first = crud.create_recurring_transaction(_rtx(10.0, DATE_FEB, account.id, category.id), session)
    rtx_second = crud.create_recurring_transaction(_rtx(20.0, DATE_FEB, account.id, category.id), session)
    rtx_third = crud.create_recurring_transaction(_rtx(30.0, DATE_FEB, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id)
    ids = [r.id for r in results]
    assert ids.index(rtx_first.id) < ids.index(rtx_second.id) < ids.index(rtx_third.id)


### PAGINATION ###

def test_rf_limit_returns_at_most_n_results(session):
    account = crud.create_account(schemas.AccountCreate(name="RFLim Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFLim Category"), session)
    for i in range(5):
        crud.create_recurring_transaction(_rtx(float(i + 1), DATE_JAN, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, limit=3)
    assert len(results) == 3

def test_rf_offset_skips_first_n_results(session):
    account = crud.create_account(schemas.AccountCreate(name="RFOff Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFOff Category"), session)
    for i in range(4):
        crud.create_recurring_transaction(_rtx(float(i + 1), DATE_JAN, account.id, category.id), session)
    all_results = crud.read_recurring_transactions_filtered(session, account_id=account.id)
    offset_results = crud.read_recurring_transactions_filtered(session, account_id=account.id, offset=2)
    assert offset_results == all_results[2:]

def test_rf_limit_and_offset_pages_correctly(session):
    account = crud.create_account(schemas.AccountCreate(name="RFPag Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFPag Category"), session)
    for i in range(6):
        crud.create_recurring_transaction(_rtx(float(i + 1), DATE_JAN, account.id, category.id), session)
    page1 = crud.read_recurring_transactions_filtered(session, account_id=account.id, limit=2, offset=0)
    page2 = crud.read_recurring_transactions_filtered(session, account_id=account.id, limit=2, offset=2)
    page3 = crud.read_recurring_transactions_filtered(session, account_id=account.id, limit=2, offset=4)
    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 2
    all_ids = [r.id for r in page1] + [r.id for r in page2] + [r.id for r in page3]
    assert len(set(all_ids)) == 6

def test_rf_offset_beyond_results_returns_empty(session):
    account = crud.create_account(schemas.AccountCreate(name="RFOffE Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFOffE Category"), session)
    crud.create_recurring_transaction(_rtx(10.0, DATE_JAN, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, offset=999)
    assert results == []

def test_rf_limit_larger_than_results_returns_all(session):
    account = crud.create_account(schemas.AccountCreate(name="RFLimL Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFLimL Category"), session)
    for i in range(3):
        crud.create_recurring_transaction(_rtx(float(i + 1), DATE_JAN, account.id, category.id), session)
    results = crud.read_recurring_transactions_filtered(session, account_id=account.id, limit=100)
    assert len(results) == 3

def test_rf_pagination_with_interval_filter(session):
    account = crud.create_account(schemas.AccountCreate(name="RFPagI Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="RFPagI Category"), session)
    for i in range(4):
        crud.create_recurring_transaction(_rtx(float(i + 1), DATE_JAN, account.id, category.id, "weekly"), session)
    crud.create_recurring_transaction(_rtx(99.0, DATE_JAN, account.id, category.id, "monthly"), session)
    page1 = crud.read_recurring_transactions_filtered(session, account_id=account.id, recurring_interval="weekly", limit=2, offset=0)
    page2 = crud.read_recurring_transactions_filtered(session, account_id=account.id, recurring_interval="weekly", limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert all(r.recurring_interval == "weekly" for r in page1 + page2)
