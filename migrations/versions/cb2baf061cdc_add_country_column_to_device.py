"""Add country column to Device

Revision ID: cb2baf061cdc
Revises: c3956a80a8d3
Create Date: 2026-01-06 12:35:03.940006

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cb2baf061cdc'
down_revision = 'c3956a80a8d3'
branch_labels = None
depends_on = None


def upgrade():
   op.add_column('devices', sa.Column('country', sa.String(length=100), nullable=True))
   op.create_index('ix_devices_country', 'devices', ['country'])


def downgrade():
    op.drop_index('ix_devices_country', table_name='devices')
    op.drop_column('devices', 'country')
