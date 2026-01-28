"""drop legacy product images tables

Revision ID: 7081af6472ea
Revises: 7af3361b9dfc
Create Date: 2026-01-27 11:23:48.867310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7081af6472ea'
down_revision: Union[str, Sequence[str], None] = '7af3361b9dfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_table("product_image_links")
    op.drop_table("product_images")
