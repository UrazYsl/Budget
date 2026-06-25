import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import crud
import schemas
from datetime import date

YEAR = 2025
MONTH = 3

def _make_tx(session, amount, year=YEAR, month=MONTH, day=1):
    account = crud.create_account(schemas.AccountCreate(name=f"Sum Account {amount} {year}{month}{day}"), session)
    category = crud.create_category(schemas.CategoryCreate(name=f"Sum Category {amount} {year}{month}{day}"), session)
    return crud.create_transaction(
        schemas.TransactionCreate(
            date=date(year, month, day),
            amount=amount,
            type="expense",
            account_id=account.id,
            category_id=category.id,
        ),
        session,
    ), account, category


# Monthly summary

def test_monthly_summary_empty(session):
    result = crud.get_monthly_summary(session, 2000, 1)
    assert result["total_expenses"] == 0.0
    assert result["transaction_count"] == 0

def test_monthly_summary_total(session):
    _make_tx(session, 100.0)
    _make_tx(session, 50.0)

    result = crud.get_monthly_summary(session, YEAR, MONTH)

    assert result["total_expenses"] >= 150.0

def test_monthly_summary_count(session):
    before = crud.get_monthly_summary(session, YEAR, MONTH)["transaction_count"]
    _make_tx(session, 10.0)
    _make_tx(session, 20.0)

    result = crud.get_monthly_summary(session, YEAR, MONTH)

    assert result["transaction_count"] == before + 2

def test_monthly_summary_excludes_other_months(session):
    _make_tx(session, 999.0, year=YEAR, month=MONTH)
    result_other = crud.get_monthly_summary(session, YEAR, MONTH + 1)
    assert result_other["total_expenses"] == 0.0
    assert result_other["total_income"] == 0.0

def test_monthly_summary_returns_correct_year_and_month(session):
    result = crud.get_monthly_summary(session, YEAR, MONTH)
    assert result["year"] == YEAR
    assert result["month"] == MONTH


# Account balances

def test_account_balances_returns_all_accounts(session):
    accounts = crud.read_accounts(session)
    balances = crud.get_account_balances(session)
    assert len(balances) >= len(accounts)

def test_account_balance_sums_transactions(session):
    account = crud.create_account(schemas.AccountCreate(name="Balance Test Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Balance Test Category"), session)
    for amount in [100.0, 200.0, 50.0]:
        crud.create_transaction(
            schemas.TransactionCreate(date=date(YEAR, MONTH, 1), amount=amount, type="expense", account_id=account.id, category_id=category.id),
            session,
        )

    balances = crud.get_account_balances(session)
    match = next(b for b in balances if b["account_id"] == account.id)
    assert match["balance"] == 350.0

def test_account_balance_zero_for_no_transactions(session):
    account = crud.create_account(schemas.AccountCreate(name="Empty Balance Account"), session)

    balances = crud.get_account_balances(session)
    match = next(b for b in balances if b["account_id"] == account.id)
    assert match["balance"] == 0.0

def test_account_balance_includes_account_name(session):
    account = crud.create_account(schemas.AccountCreate(name="Named Balance Account"), session)

    balances = crud.get_account_balances(session)
    match = next(b for b in balances if b["account_id"] == account.id)
    assert match["account_name"] == "Named Balance Account"


# Category totals

def test_category_totals_includes_all_categories(session):
    categories = crud.read_categories(session)
    totals = crud.get_category_totals(session, YEAR, MONTH)
    assert len(totals) >= len(categories)

def test_category_total_sums_correctly(session):
    account = crud.create_account(schemas.AccountCreate(name="Cat Total Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Cat Total Category"), session)
    for amount in [30.0, 70.0]:
        crud.create_transaction(
            schemas.TransactionCreate(date=date(YEAR, MONTH, 1), amount=amount, type="expense", account_id=account.id, category_id=category.id),
            session,
        )

    totals = crud.get_category_totals(session, YEAR, MONTH)
    match = next(t for t in totals if t["category_id"] == category.id)
    assert match["total"] == 100.0

def test_category_total_zero_for_empty_month(session):
    category = crud.create_category(schemas.CategoryCreate(name="Empty Month Category"), session)

    totals = crud.get_category_totals(session, 1999, 1)
    match = next((t for t in totals if t["category_id"] == category.id), None)
    if match:
        assert match["total"] == 0.0

def test_category_total_excludes_other_months(session):
    account = crud.create_account(schemas.AccountCreate(name="Cat Excl Account"), session)
    category = crud.create_category(schemas.CategoryCreate(name="Cat Excl Category"), session)
    crud.create_transaction(
        schemas.TransactionCreate(date=date(YEAR, MONTH, 1), amount=500.0, type="expense", account_id=account.id, category_id=category.id),
        session,
    )

    totals_other = crud.get_category_totals(session, YEAR, MONTH + 1)
    match = next((t for t in totals_other if t["category_id"] == category.id), None)
    if match:
        assert match["total"] == 0.0
