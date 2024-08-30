"""Add is_favorite to media_items

Revision ID: add_is_favorite_to_media_items
Revises: create_logs_table
Create Date: 2023-08-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_is_favorite_to_media_items'
down_revision = 'create_logs_table'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('media_items', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'))

def downgrade():
    op.drop_column('media_items', 'is_favorite')