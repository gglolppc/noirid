"""add support questions and allow unassigned product images

Revision ID: 9b5d1d4b0b1e
Revises: 1df44e74c7ed
Create Date: 2024-05-05 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b5d1d4b0b1e"
down_revision = "1df44e74c7ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(length=200), nullable=False),
        sa.Column("customer_email", sa.String(length=320), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.alter_column("product_images", "product_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column("product_images", "product_id", existing_type=sa.Integer(), nullable=False)
    op.drop_table("support_questions")
