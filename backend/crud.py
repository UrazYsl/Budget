from datetime import date
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from models import Account, Category, Transaction, RecurringTransaction
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
        account_id=tx.account_id,
        category_id=tx.category_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

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
    recurring.recurring_interval = rtx.recurring_interval.value
    recurring.next_run_date = rtx.next_run_date
    recurring.account_id = rtx.account_id
    recurring.category_id = rtx.category_id
    db.commit()
    return 1

### FILTERS ###
# The parameters are optional, to allow for combinations of filters. 
# If a parameter is None, it won't be applied.
def read_transactions_filtered(
    db: Session,
    account_id: int | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Transaction]:
    stmt = select(Transaction)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)
    if start_date is not None:
        stmt = stmt.where(Transaction.date >= start_date)
    if end_date is not None:
        stmt = stmt.where(Transaction.date <= end_date)
    stmt = stmt.order_by(Transaction.date.desc(), Transaction.id.desc()).offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return db.scalars(stmt).all()
