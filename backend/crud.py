from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, delete, func, extract
from sqlalchemy.orm import Session
from models import Account, Budget, Category, Transaction, RecurringTransaction
from schemas import AccountCreate, CategoryCreate

def create_account(account: AccountCreate, db: Session) -> Account:
    account = Account(name=account.name)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

def read_accounts(db: Session) -> list[Account]:
    return db.scalars(select(Account).order_by(Account.id)).all()

def delete_account(account_id: int, db: Session) -> int:
    account = db.get(Account, account_id)
    if account is None:
        return 0
    db.delete(account)
    db.commit()
    return 1

def update_account(account_id: int, new_name: str, db: Session) -> int:
    account = db.get(Account, account_id)
    if account is None:
        return 0
    account.name = new_name
    db.commit()
    return 1

def create_category(category: CategoryCreate, db: Session) -> Category:
    category = Category(name=category.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

def read_categories(db: Session) -> list[Category]:
    return db.scalars(select(Category).order_by(Category.id)).all()

def delete_category(category_id: int, db: Session):
    # passive_deletes=True on the relationship means SQLAlchemy won't touch FK rows;
    # the DB ON DELETE SET DEFAULT fires and reassigns transactions to Misc.
    category = db.get(Category, category_id)
    if category is None:
        return 0
    db.delete(category)
    db.commit()
    return 1

def update_category(category_id: int, new_name: str, db: Session):
    category = db.get(Category, category_id)
    if category is None:
        return 0
    category.name = new_name
    db.commit()
    return 1

def create_transaction(tx, db: Session) -> Transaction:
    transaction = Transaction(
        date=tx.date,
        amount=tx.amount,
        type=tx.type.value,
        account_id=tx.account_id,
        category_id=tx.category_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def get_transaction(db: Session, tx_id: int) -> Transaction | None:
    return db.get(Transaction, tx_id)

def set_receipt_path(db: Session, tx_id: int, path: str | None) -> int:
    tx = db.get(Transaction, tx_id)
    if tx is None:
        return 0
    tx.receipt_path = path
    db.commit()
    return 1

def read_transactions(db: Session) -> list[Transaction]:
    return db.scalars(
        select(Transaction)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
    ).all()

def update_transaction(tx_id: int, tx, db: Session) -> int:
    transaction = db.get(Transaction, tx_id)
    if transaction is None:
        return 0
    transaction.date = tx.date
    transaction.amount = tx.amount
    transaction.type = tx.type.value
    transaction.account_id = tx.account_id
    transaction.category_id = tx.category_id
    db.commit()
    return 1

def delete_transaction(tx_id: int, db: Session):
    result = db.execute(delete(Transaction).where(Transaction.id == tx_id))
    db.commit()
    return result.rowcount

def create_recurring_transaction(rtx, db: Session) -> RecurringTransaction:
    rtx_obj = RecurringTransaction(
        amount=rtx.amount,
        type=rtx.type.value,
        recurring_interval=rtx.recurring_interval.value,
        next_run_date=rtx.next_run_date,
        account_id=rtx.account_id,
        category_id=rtx.category_id,
    )
    db.add(rtx_obj)
    db.commit()
    db.refresh(rtx_obj)
    return rtx_obj

def read_recurring_transactions(db: Session) -> list[RecurringTransaction]:
    return db.scalars(
        select(RecurringTransaction)
        .order_by(RecurringTransaction.next_run_date.asc(), RecurringTransaction.id.asc())
    ).all()

def read_recurring_transactions_filtered(
    db: Session,
    account_id: int | None = None,
    category_id: int | None = None,
    recurring_interval: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[RecurringTransaction]:
    stmt = select(RecurringTransaction)
    if account_id is not None:
        stmt = stmt.where(RecurringTransaction.account_id == account_id)
    if category_id is not None:
        stmt = stmt.where(RecurringTransaction.category_id == category_id)
    if recurring_interval is not None:
        stmt = stmt.where(RecurringTransaction.recurring_interval == recurring_interval)
    if start_date is not None:
        stmt = stmt.where(RecurringTransaction.next_run_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(RecurringTransaction.next_run_date <= end_date)
    stmt = stmt.order_by(RecurringTransaction.next_run_date.asc(), RecurringTransaction.id.asc()).offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return db.scalars(stmt).all()

def delete_recurring_transaction(rtx_id: int, db: Session):
    result = db.execute(delete(RecurringTransaction).where(RecurringTransaction.id == rtx_id))
    db.commit()
    return result.rowcount

def update_recurring_transaction(rtx_id: int, rtx, db: Session) -> int:
    recurring = db.get(RecurringTransaction, rtx_id)
    if recurring is None:
        return 0
    recurring.amount = rtx.amount
    recurring.type = rtx.type.value
    recurring.recurring_interval = rtx.recurring_interval.value
    recurring.next_run_date = rtx.next_run_date
    recurring.account_id = rtx.account_id
    recurring.category_id = rtx.category_id
    db.commit()
    return 1

def _advance_date(d: date, interval: str) -> date:
    if interval == "daily":
        return d + timedelta(days=1)
    if interval == "weekly":
        return d + timedelta(weeks=1)
    if interval == "monthly":
        return d + relativedelta(months=1)
    if interval == "yearly":
        return d + relativedelta(years=1)

def process_due_recurring_transactions(db: Session) -> int:
    today = date.today()
    due = db.scalars(
        select(RecurringTransaction).where(RecurringTransaction.next_run_date <= today)
    ).all()

    count = 0
    for rtx in due:
        while rtx.next_run_date <= today:
            db.add(Transaction(
                date=rtx.next_run_date,
                amount=rtx.amount,
                type=rtx.type,
                account_id=rtx.account_id,
                category_id=rtx.category_id,
            ))
            rtx.next_run_date = _advance_date(rtx.next_run_date, rtx.recurring_interval)
            count += 1

    db.commit()
    return count


### SUMMARIES ###

def get_monthly_summary(db: Session, year: int, month: int) -> dict:
    rows = db.execute(
        select(
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0.0).label("total"),
            func.count(Transaction.id).label("transaction_count"),
        ).where(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
        ).group_by(Transaction.type)
    ).all()
    totals = {row.type: row.total for row in rows}
    counts = {row.type: row.transaction_count for row in rows}
    total_income = totals.get("income", 0.0)
    total_expenses = totals.get("expense", 0.0)
    return {
        "year": year,
        "month": month,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net": total_income - total_expenses,
        "transaction_count": sum(counts.values()),
    }

def get_account_balances(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            Account.id.label("account_id"),
            Account.name.label("account_name"),
            func.coalesce(func.sum(Transaction.amount), 0.0).label("balance"),
        )
        .outerjoin(Transaction, Transaction.account_id == Account.id)
        .group_by(Account.id, Account.name)
        .order_by(Account.id)
    ).all()
    return [{"account_id": r.account_id, "account_name": r.account_name, "balance": r.balance} for r in rows]

def get_upcoming_recurring(db: Session, days: int = 7) -> list[RecurringTransaction]:
    today = date.today()
    cutoff = today + timedelta(days=days)
    return db.scalars(
        select(RecurringTransaction)
        .where(RecurringTransaction.next_run_date >= today)
        .where(RecurringTransaction.next_run_date <= cutoff)
        .order_by(RecurringTransaction.next_run_date.asc())
    ).all()

def get_category_totals(db: Session, year: int, month: int) -> list[dict]:
    rows = db.execute(
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.coalesce(func.sum(Transaction.amount), 0.0).label("total"),
        )
        .outerjoin(
            Transaction,
            (Transaction.category_id == Category.id)
            & (extract("year", Transaction.date) == year)
            & (extract("month", Transaction.date) == month),
        )
        .group_by(Category.id, Category.name)
        .order_by(Category.id)
    ).all()
    return [{"category_id": r.category_id, "category_name": r.category_name, "total": r.total} for r in rows]


### FILTERS ###
# The parameters are optional, to allow for combinations of filters. 
# If a parameter is None, it won't be applied.
def read_transactions_filtered(
    db: Session,
    account_id: int | None = None,
    category_id: int | None = None,
    tx_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Transaction]:
    stmt = select(Transaction)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)
    if tx_type is not None:
        stmt = stmt.where(Transaction.type == tx_type)
    if start_date is not None:
        stmt = stmt.where(Transaction.date >= start_date)
    if end_date is not None:
        stmt = stmt.where(Transaction.date <= end_date)
    if min_amount is not None:
        stmt = stmt.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        stmt = stmt.where(Transaction.amount <= max_amount)
    stmt = stmt.order_by(Transaction.date.desc(), Transaction.id.desc()).offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return db.scalars(stmt).all()


def get_budgets(db: Session) -> list[Budget]:
    return db.scalars(select(Budget).order_by(Budget.category_id)).all()

def upsert_budget(db: Session, category_id: int, amount: float) -> Budget:
    b = db.scalars(select(Budget).where(Budget.category_id == category_id)).first()
    if b:
        b.amount = amount
    else:
        b = Budget(category_id=category_id, amount=amount)
        db.add(b)
    db.commit()
    db.refresh(b)
    return b

def delete_budget(db: Session, budget_id: int) -> int:
    b = db.get(Budget, budget_id)
    if b is None:
        return 0
    db.delete(b)
    db.commit()
    return 1
