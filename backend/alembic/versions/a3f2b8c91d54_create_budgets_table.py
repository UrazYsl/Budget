"""create budgets table

Revision ID: a3f2b8c91d54
Revises: c7e4a1f30b92
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = 'a3f2b8c91d54'
down_revision = 'c7e4a1f30b92'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id'),
    )
    op.create_index('ix_budgets_id', 'budgets', ['id'])


def downgrade():
    op.drop_index('ix_budgets_id', table_name='budgets')
    op.drop_table('budgets')
