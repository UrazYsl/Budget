from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Account, Category, Transaction, RecurringTransaction
from schemas import AccountCreate, CategoryCreate

def create_account(account: AccountCreate, db: Session) -> Account:
    account = Account(name=account.name)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

def read_accounts(db: Session) -> list[Account]:
    return db.query(Account).order_by(Account.id).all()

def delete_account(account_id: int, db: Session) -> int:
    # It will ask for confirmation in the UI, so we can assume the user knows what they're doing.
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None:
        return 0
    _check_recurring_transactions(account_id, db)
    db.delete(account)
    db.commit()
    return 1

def update_account(account_id: int, new_name: str, db: Session) -> int:
    account = db.query(Account).filter(Account.id == account_id).first()
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
    return db.query(Category).order_by(Category.id).all()

def delete_category(category_id: int, db: Session):
    # It will ask for confirmation in the UI, so we can assume the user knows what they're doing.
    # Will also change the category of any transactions with this category to misc, so we don't have to worry about orphaned transactions.
    result = db.execute(
        text("DELETE FROM categories WHERE id = :id"),
        {"id": category_id},
    )
    db.commit()
    return result.rowcount

def update_category(category_id: int, new_name: str, db: Session):
    category = db.query(Category).filter(Category.id == category_id).first()
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

def read_transactions(db: Session):
    result = db.execute(
        text("""
            SELECT id, date, amount, account_id, category_id
            FROM transactions
            ORDER BY date DESC, id DESC
        """)
    )
    return result.mappings().all()

def delete_transaction(tx_id: int, db: Session):
    result = db.execute(
        text("DELETE FROM transactions WHERE id = :id"),
        {"id": tx_id},
    )
    db.commit()
    return result.rowcount


def create_recurring_transaction(rtx, db: Session):
    result = db.execute(
        text("""
            INSERT INTO recurring_transactions
                (amount, recurring_interval, next_run_date, account_id, category_id)
            VALUES (:amount, :recurring_interval, :next_run_date, :account_id, :category_id)
            RETURNING id, amount, recurring_interval, next_run_date, account_id, category_id
        """),
        {
            "amount": rtx.amount,
            "recurring_interval": rtx.recurring_interval.value,
            "next_run_date": rtx.next_run_date,
            "account_id": rtx.account_id,
            "category_id": rtx.category_id,
        },
    )
    db.commit()
    return result.mappings().one()

def read_recurring_transactions(db: Session):
    result = db.execute(
        text("""
            SELECT id, amount, recurring_interval, next_run_date, account_id, category_id
            FROM recurring_transactions
            ORDER BY next_run_date ASC, id ASC
        """)
    )
    return result.mappings().all()

def _check_recurring_transactions(account_id: int, db: Session) -> None:
    # Check if there are any recurring transactions associated with this account. If there are, we can't delete the account.
    transactions = db.query(RecurringTransaction).filter(RecurringTransaction.account_id == account_id).all()
    for tx in transactions:
        db.delete(tx)

def delete_recurring_transaction(rtx_id: int, db: Session):
    result = db.execute(
        text("DELETE FROM recurring_transactions WHERE id = :id"),
        {"id": rtx_id},
    )
    db.commit()
    return result.rowcount
