"""add product image links

Revision ID: b2c1b2c6d2a5
Revises: 9f6c6f0a28fd
Create Date: 2024-05-05 13:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2c1b2c6d2a5"
down_revision = "9f6c6f0a28fd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_image_links",
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("image_id", sa.Integer(), sa.ForeignKey("product_images.id", ondelete="CASCADE"), primary_key=True),
    )
    op.execute(
        """
        INSERT INTO product_image_links (product_id, image_id)
        SELECT product_id, id
        FROM product_images
        WHERE product_id IS NOT NULL
        """
    )
    op.drop_index("ix_product_images_product_id", table_name="product_images")
    op.drop_column("product_images", "product_id")


def downgrade() -> None:
    op.add_column("product_images", sa.Column("product_id", sa.Integer(), nullable=True))
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])
    op.execute(
        """
        UPDATE product_images
        SET product_id = link.product_id
        FROM product_image_links AS link
        WHERE product_images.id = link.image_id
        """
    )
    op.drop_table("product_image_links")
