"""empty message

Revision ID: 516db450c016
Revises: 3b2e9a1f0c24, 5c2c3e9f0b6a
Create Date: 2026-01-23 11:25:16.269946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '516db450c016'
down_revision: Union[str, Sequence[str], None] = ('3b2e9a1f0c24', '5c2c3e9f0b6a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
