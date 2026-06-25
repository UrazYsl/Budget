"""add receipt_path to transactions

Revision ID: c7e4a1f30b92
Revises: 18aa86bab5df
Create Date: 2026-06-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7e4a1f30b92'
down_revision: Union[str, Sequence[str], None] = '18aa86bab5df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('receipt_path', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('transactions', 'receipt_path')
