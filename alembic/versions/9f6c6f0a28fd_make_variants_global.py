"""make variants global

Revision ID: 9f6c6f0a28fd
Revises: 9b5d1d4b0b1e
Create Date: 2024-05-05 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f6c6f0a28fd"
down_revision = "9b5d1d4b0b1e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_variant_product_device", "variants", type_="unique")
    op.drop_index("ix_variant_product_active", table_name="variants")
    op.drop_index("ix_variant_product_brand", table_name="variants")
    op.alter_column("variants", "product_id", existing_type=sa.Integer(), nullable=True)
    op.create_unique_constraint("uq_variant_device", "variants", ["device_brand", "device_model"])
    op.create_index("ix_variant_brand_active", "variants", ["device_brand", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_variant_brand_active", table_name="variants")
    op.drop_constraint("uq_variant_device", "variants", type_="unique")
    op.alter_column("variants", "product_id", existing_type=sa.Integer(), nullable=False)
    op.create_unique_constraint(
        "uq_variant_product_device",
        "variants",
        ["product_id", "device_brand", "device_model"],
    )
    op.create_index("ix_variant_product_active", "variants", ["product_id", "is_active"])
    op.create_index("ix_variant_product_brand", "variants", ["product_id", "device_brand", "is_active"])
