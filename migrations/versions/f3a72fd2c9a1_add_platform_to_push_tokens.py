"""add platform to push tokens

Revision ID: f3a72fd2c9a1
Revises: 9d0b55b77143
Create Date: 2026-06-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f3a72fd2c9a1'
down_revision = '9d0b55b77143'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("""
        DO $$
        BEGIN
            CREATE TYPE platform AS ENUM ('WEB', 'IOS', 'ANDROID', 'MACOS', 'WINDOWS', 'UNKNOWN');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """)
        platform_type = postgresql.ENUM(
            'WEB',
            'IOS',
            'ANDROID',
            'MACOS',
            'WINDOWS',
            'UNKNOWN',
            name='platform',
            create_type=False
        )
    else:
        platform_type = sa.Enum(
            'WEB',
            'IOS',
            'ANDROID',
            'MACOS',
            'WINDOWS',
            'UNKNOWN',
            name='platform'
        )

    with op.batch_alter_table('pushTokens', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'platform',
                platform_type,
                nullable=False,
                server_default='UNKNOWN'
            )
        )
        batch_op.create_index(batch_op.f('ix_pushTokens_platform'), ['platform'], unique=False)

    with op.batch_alter_table('pushTokens', schema=None) as batch_op:
        batch_op.alter_column('platform', server_default=None)


def downgrade():
    with op.batch_alter_table('pushTokens', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pushTokens_platform'))
        batch_op.drop_column('platform')
