"""empty message

Revision ID: 01263772c3ba
Revises: 9f6c6f0a28fd, 0a1615ca65eb
Create Date: 2026-01-23 20:35:17.353426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01263772c3ba'
down_revision: Union[str, Sequence[str], None] = ('9f6c6f0a28fd', '0a1615ca65eb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
