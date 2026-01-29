"""add confirmation_email_sent_at to order1

Revision ID: c4d80660def3
Revises: ebc234ba1d11
Create Date: 2026-01-29 12:38:51.675588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d80660def3'
down_revision: Union[str, Sequence[str], None] = 'ebc234ba1d11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
