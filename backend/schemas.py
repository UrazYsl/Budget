from datetime import date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class TransactionType(str, Enum):
    income = "income"
    expense = "expense"

class Interval(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"

class AccountCreate(BaseModel):
    name: str

class AccountOut(AccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class CategoryCreate(BaseModel):
    name: str

class CategoryOut(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class TransactionCreate(BaseModel):
    date: date
    amount: float = Field(gt=0)
    type: TransactionType
    account_id: int
    category_id: int

class TransactionOut(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    receipt_path: str | None = None

class MonthlySummary(BaseModel):
    year: int
    month: int
    total_income: float
    total_expenses: float
    net: float
    transaction_count: int

class AccountBalance(BaseModel):
    account_id: int
    account_name: str
    balance: float

class CategoryTotal(BaseModel):
    category_id: int
    category_name: str
    total: float


class RecurringTransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    type: TransactionType
    recurring_interval: Interval
    next_run_date: date
    account_id: int
    category_id: int

class RecurringTransactionOut(RecurringTransactionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
