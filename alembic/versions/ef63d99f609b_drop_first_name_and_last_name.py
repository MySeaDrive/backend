"""Drop first_name and last_name

Revision ID: ef63d99f609b
Revises: 4c822fcdbe5d
Create Date: 2024-09-29 00:09:19.599554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ef63d99f609b'
down_revision: Union[str, None] = '4c822fcdbe5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')

def downgrade():
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))