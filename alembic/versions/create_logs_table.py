"""create logs table

Revision ID: create_logs_table
Revises: <previous_revision_id>
Create Date: 2023-08-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = 'create_logs_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dive_id', sa.Integer(), nullable=False),
        sa.Column('starting_air', sa.Integer(), nullable=True),
        sa.Column('ending_air', sa.Integer(), nullable=True),
        sa.Column('dive_start_time', sa.DateTime(), nullable=True),
        sa.Column('dive_duration', sa.Integer(), nullable=True),
        sa.Column('max_depth', sa.Float(), nullable=True),
        sa.Column('visibility', sa.Float(), nullable=True),
        sa.Column('water_temperature', sa.Float(), nullable=True),
        sa.Column('wetsuit_thickness', sa.Integer(), nullable=True),
        sa.Column('wetsuit_type', sa.String(), nullable=True),
        sa.Column('weights', sa.Float(), nullable=True),
        sa.Column('fish_ids', JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dive_id'], ['dives.id'], ),
        sa.UniqueConstraint('dive_id')
    )

def downgrade():
    op.drop_table('logs')