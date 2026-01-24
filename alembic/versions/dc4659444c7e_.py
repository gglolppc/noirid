"""empty message

Revision ID: dc4659444c7e
Revises: 01263772c3ba, b2c1b2c6d2a5
Create Date: 2026-01-24 10:16:33.508343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc4659444c7e'
down_revision: Union[str, Sequence[str], None] = ('01263772c3ba', 'b2c1b2c6d2a5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
