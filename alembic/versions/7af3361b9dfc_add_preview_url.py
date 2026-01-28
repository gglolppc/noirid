"""add preview_url

Revision ID: 7af3361b9dfc
Revises: c1d8f1b0a6c2
Create Date: 2026-01-27 11:23:21.170420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7af3361b9dfc'
down_revision: Union[str, Sequence[str], None] = 'c1d8f1b0a6c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('order_items', sa.Column('preview_url', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('order_items', 'preview_url')
