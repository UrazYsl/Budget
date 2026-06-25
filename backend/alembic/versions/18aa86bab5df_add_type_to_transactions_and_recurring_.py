"""add type to transactions and recurring transactions

Revision ID: 18aa86bab5df
Revises: 018c118943ee
Create Date: 2026-06-25 11:12:23.891829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18aa86bab5df'
down_revision: Union[str, Sequence[str], None] = '018c118943ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('type', sa.String(), nullable=False, server_default='expense'))
    op.add_column('recurring_transactions', sa.Column('type', sa.String(), nullable=False, server_default='expense'))


def downgrade() -> None:
    op.drop_column('transactions', 'type')
    op.drop_column('recurring_transactions', 'type')
