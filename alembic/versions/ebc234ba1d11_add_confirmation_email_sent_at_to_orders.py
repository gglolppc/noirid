"""add confirmation_email_sent_at to orders

Revision ID: ebc234ba1d11
Revises: aa2f41111c38
Create Date: 2026-01-29 12:35:43.325093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebc234ba1d11'
down_revision: Union[str, Sequence[str], None] = 'aa2f41111c38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
