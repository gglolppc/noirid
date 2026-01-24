"""empty message

Revision ID: 0a1615ca65eb
Revises: 516db450c016, 9b5d1d4b0b1e
Create Date: 2026-01-23 16:16:29.290499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a1615ca65eb'
down_revision: Union[str, Sequence[str], None] = ('516db450c016', '9b5d1d4b0b1e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
