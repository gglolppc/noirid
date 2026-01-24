"""add product images json

Revision ID: c1d8f1b0a6c2
Revises: e46e1dc1c2c7
Create Date: 2026-02-01 10:12:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c1d8f1b0a6c2"
down_revision: Union[str, Sequence[str], None] = "e46e1dc1c2c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "images",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.execute(
        """
        UPDATE products
        SET images = COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'id',
                        row_number() OVER (ORDER BY pil.sort, pi.id) - 1,
                        'url',
                        pi.url
                    )
                    ORDER BY pil.sort, pi.id
                )
                FROM product_image_links pil
                JOIN product_images pi ON pi.id = pil.image_id
                WHERE pil.product_id = products.id
            ),
            '[]'::jsonb
        )
        """
    )
    op.alter_column("products", "images", server_default=None)


def downgrade() -> None:
    op.drop_column("products", "images")
