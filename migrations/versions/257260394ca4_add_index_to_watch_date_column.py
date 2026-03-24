"""Add index to watch_date column

Revision ID: 257260394ca4
Revises: cb2baf061cdc
Create Date: 2026-03-24 11:27:30.103952

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '257260394ca4'
down_revision = 'cb2baf061cdc'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column
    op.add_column('devices', sa.Column('watch_date', sa.DateTime(), nullable=True))
    # Create an index on the column
    op.create_index('ix_devices_watch_date', 'devices', ['watch_date'], unique=False)

def downgrade():
    # Drop the index first
    op.drop_index('ix_devices_watch_date', table_name='devices')
    # Drop the column
    op.drop_column('devices', 'watch_date')
