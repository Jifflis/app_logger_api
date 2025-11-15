"""Introduce LogTag model, add log_tag_id, migrate old tags

Revision ID: c3956a80a8d3
Revises: 
Create Date: 2025-11-14 09:49:05.841614

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3956a80a8d3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create log_tags table
    op.create_table(
        'log_tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tag', sa.String(length=100), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id']),
        sa.UniqueConstraint('tag', 'project_id', name='uq_tag_per_project')
    )

    # 2. Add new column to device_logs
    op.add_column('device_logs', sa.Column('log_tag_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_device_logs_log_tag_id',
        'device_logs',
        'log_tags',
        ['log_tag_id'],
        ['id']
    )

    # 3. Migrate existing tag values into log_tags table
    #    and link device_logs.log_tag_id
    connection = op.get_bind()

    # Fetch all existing device logs with tags
    rows = connection.execute(sa.text("""
        SELECT log_id, project_id, tag
        FROM device_logs
        WHERE tag IS NOT NULL AND TRIM(tag) <> ''
    """)).fetchall()

    inserted = {}  # key=(project_id, tag), value=id

    for log_id, project_id, tag in rows:
        key = (project_id, tag)

        if key not in inserted:
            result = connection.execute(sa.text("""
                INSERT INTO log_tags (tag, project_id)
                VALUES (:tag, :project_id)
                RETURNING id
            """), {"tag": tag, "project_id": project_id})
            inserted[key] = result.scalar()

        # update device_logs.log_tag_id
        connection.execute(sa.text("""
            UPDATE device_logs
            SET log_tag_id = :log_tag_id
            WHERE log_id = :log_id
        """), {"log_tag_id": inserted[key], "log_id": log_id})

    # 4. Drop old string column
    op.drop_column('device_logs', 'tag')


def downgrade():
    # Reverse order
    op.add_column('device_logs', sa.Column('tag', sa.String(length=100)))

    connection = op.get_bind()

    # restore old tags
    rows = connection.execute(sa.text("""
        SELECT log_id, log_tag_id
        FROM device_logs
        WHERE log_tag_id IS NOT NULL AND TRIM(tag) <> ''
    """)).fetchall()

    for log_id, log_tag_id in rows:
        tag_row = connection.execute(sa.text("""
            SELECT tag FROM log_tags WHERE id = :id
        """), {"id": log_tag_id}).fetchone()

        if tag_row:
            connection.execute(sa.text("""
                UPDATE device_logs
                SET tag = :tag
                WHERE log_id = :log_id
            """), {"tag": tag_row.tag, "log_id": log_id})

    # drop new schema items
    op.drop_constraint('fk_device_logs_log_tag_id', 'device_logs', type_='foreignkey')
    op.drop_column('device_logs', 'log_tag_id')
    op.drop_table('log_tags')
