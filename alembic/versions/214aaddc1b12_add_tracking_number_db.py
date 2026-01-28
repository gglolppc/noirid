"""add tracking_number_db

Revision ID: 214aaddc1b12
Revises: 768df386a2fc
Create Date: 2026-01-27 14:21:53.088636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '214aaddc1b12'
down_revision: Union[str, Sequence[str], None] = '768df386a2fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
