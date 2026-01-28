"""add tracking_number_db

Revision ID: 768df386a2fc
Revises: 7081af6472ea
Create Date: 2026-01-27 14:21:14.619569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '768df386a2fc'
down_revision: Union[str, Sequence[str], None] = '7081af6472ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
