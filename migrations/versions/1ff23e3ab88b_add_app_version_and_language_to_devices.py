"""Add app_version and language to devices

Revision ID: 1ff23e3ab88b
Revises: 257260394ca4
Create Date: 2026-06-05 20:22:06.011130

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ff23e3ab88b'
down_revision = '257260394ca4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('app_version', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('language', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.drop_column('language')
        batch_op.drop_column('app_version')
