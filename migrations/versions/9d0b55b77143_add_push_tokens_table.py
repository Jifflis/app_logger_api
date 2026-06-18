"""add push tokens table

Revision ID: 9d0b55b77143
Revises: 4bb5ba31dcf2
Create Date: 2026-06-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d0b55b77143'
down_revision = '4bb5ba31dcf2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pushTokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.String(length=100), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['devices.instance_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instance_id', 'token', name='uq_device_push_token')
    )
    with op.batch_alter_table('pushTokens', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pushTokens_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_pushTokens_instance_id'), ['instance_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pushTokens_token'), ['token'], unique=False)


def downgrade():
    with op.batch_alter_table('pushTokens', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pushTokens_token'))
        batch_op.drop_index(batch_op.f('ix_pushTokens_instance_id'))
        batch_op.drop_index(batch_op.f('ix_pushTokens_created_at'))

    op.drop_table('pushTokens')
