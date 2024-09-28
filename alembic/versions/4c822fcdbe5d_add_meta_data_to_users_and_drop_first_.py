"""Add meta_data to users and drop first_name and last_name

Revision ID: 4c822fcdbe5d
Revises: add_is_favorite_to_media_items
Create Date: 2024-09-29 00:06:45.575338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '4c822fcdbe5d'
down_revision: Union[str, None] = 'add_is_favorite_to_media_items'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('users', sa.Column('raw_app_meta_data', JSONB(), nullable=True))
    op.add_column('users', sa.Column('raw_user_meta_data', JSONB(), nullable=True))

def downgrade():
    op.drop_column('users', 'raw_user_meta_data')
    op.drop_column('users', 'raw_app_meta_data')