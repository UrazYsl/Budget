from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    # delete account => delete its transactions (DB FK handles it)
    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete",
        passive_deletes=True,
    )
    recurring_transactions = relationship(
        "RecurringTransaction",
        back_populates="account",
        cascade="all, delete",
        passive_deletes=True,
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    transactions = relationship(
        "Transaction",
        back_populates="category",
        passive_deletes=True,
    )
    recurring_transactions = relationship(
        "RecurringTransaction",
        back_populates="category",
        passive_deletes=True,
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # income | expense

    # account delete -> cascade
    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # category delete -> set default (Misc)
    # Misc is always seeded first so it gets id=1; SET DEFAULT falls back to it on category delete
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET DEFAULT"),
        nullable=False,
        index=True,
        server_default='1',
    )

    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class RecurringTransaction(Base):
    """Schedule: job copies these into transactions on next_run_date."""
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # income | expense
    recurring_interval = Column(String, nullable=False)  # daily, weekly, monthly, yearly
    next_run_date = Column(Date, nullable=False)

    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    account = relationship("Account", back_populates="recurring_transactions")
    category = relationship("Category", back_populates="recurring_transactions")
