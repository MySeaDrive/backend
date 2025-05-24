"""add cascade delete on logs.dive_id

Revision ID: 44402b5cc63e
Revises: e8c7d572acc0
Create Date: 2025-05-24 23:22:11.700720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44402b5cc63e'
down_revision: Union[str, None] = 'e8c7d572acc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # drop the old FK
    op.drop_constraint('logs_dive_id_fkey', 'logs', type_='foreignkey')
    # re-create with ON DELETE CASCADE
    op.create_foreign_key(
        'logs_dive_id_fkey',
        'logs', 'dives',
        ['dive_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('logs_dive_id_fkey', 'logs', type_='foreignkey')
    op.create_foreign_key(
        'logs_dive_id_fkey',
        'logs', 'dives',
        ['dive_id'], ['id']
        # no ondelete
    )
