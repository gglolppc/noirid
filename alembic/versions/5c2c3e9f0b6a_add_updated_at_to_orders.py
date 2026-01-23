"""add updated_at to orders

Revision ID: 5c2c3e9f0b6a
Revises: 1df44e74c7ed
Create Date: 2026-02-05 10:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5c2c3e9f0b6a"
down_revision: Union[str, Sequence[str], None] = "1df44e74c7ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "orders",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "updated_at")
