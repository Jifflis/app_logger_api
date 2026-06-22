"""add instances table

Revision ID: a84f7c2d9e31
Revises: f3a72fd2c9a1
Create Date: 2026-06-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a84f7c2d9e31'
down_revision = 'f3a72fd2c9a1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instance_id', name='uq_instances_instance_id')
    )
    with op.batch_alter_table('instances', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_instances_instance_id'), ['instance_id'], unique=False)


def downgrade():
    with op.batch_alter_table('instances', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_instances_instance_id'))

    op.drop_table('instances')
