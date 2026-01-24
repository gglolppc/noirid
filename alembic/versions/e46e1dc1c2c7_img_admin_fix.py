"""img admin fix

Revision ID: e46e1dc1c2c7
Revises: dc4659444c7e
Create Date: 2026-01-24 10:30:53.076196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e46e1dc1c2c7"
down_revision: Union[str, Sequence[str], None] = "dc4659444c7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1) orders.payment_status: убрать NULL перед NOT NULL ---
    # Выбери правильный дефолт под свою логику. Я ставлю 'pending'.
    op.execute("UPDATE orders SET payment_status = 'pending' WHERE payment_status IS NULL")

    op.alter_column(
        "orders",
        "payment_status",
        existing_type=sa.VARCHAR(length=32),
        server_default=sa.text("'pending'"),
        nullable=False,
    )

    # --- 2) payments.raw_payload: убрать NULL перед NOT NULL ---
    # Ставим пустой объект, чтобы не падало.
    op.execute("UPDATE payments SET raw_payload = '{}'::jsonb WHERE raw_payload IS NULL")

    op.alter_column(
        "payments",
        "raw_payload",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    # --- 3) product_image_links: добавить sort/role безопасно ---
    # Добавляем с дефолтами, иначе упадет на существующих строках.
    op.add_column(
        "product_image_links",
        sa.Column("sort", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "product_image_links",
        sa.Column("role", sa.String(length=32), nullable=False, server_default=sa.text("'gallery'")),
    )

    # Если хочешь: убрать server_default после миграции (оставить только NOT NULL).
    # Обычно я бы оставил дефолт, но решай сам.
    op.alter_column("product_image_links", "sort", server_default=None)
    op.alter_column("product_image_links", "role", server_default=None)

    # --- support_questions.created_at (как было, норм) ---
    op.alter_column(
        "support_questions",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )


def downgrade() -> None:
    # --- support_questions.created_at ---
    op.alter_column(
        "support_questions",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )

    # --- product_image_links ---
    op.drop_column("product_image_links", "role")
    op.drop_column("product_image_links", "sort")

    # --- payments.raw_payload ---
    op.alter_column(
        "payments",
        "raw_payload",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=None,
        nullable=True,
    )

    # --- orders.payment_status ---
    op.alter_column(
        "orders",
        "payment_status",
        existing_type=sa.VARCHAR(length=32),
        server_default=None,
        nullable=True,
    )
