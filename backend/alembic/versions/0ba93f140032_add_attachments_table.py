"""add attachments table

Revision ID: 0ba93f140032
Revises: 6e0c9fa9eb3b
Create Date: 2026-05-22 01:02:01.231534

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0ba93f140032'
down_revision: Union[str, Sequence[str], None] = '6e0c9fa9eb3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('uploader_name', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id']),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attachments_id'), 'attachments', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_attachments_id'), table_name='attachments')
    op.drop_table('attachments')
