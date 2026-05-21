"""add_file_locks

Revision ID: 6e0c9fa9eb3b
Revises: ecc32d9a488e
Create Date: 2026-05-21 20:29:48.832223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e0c9fa9eb3b'
down_revision: Union[str, Sequence[str], None] = 'ecc32d9a488e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('file_locks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('agent_name', sa.String(), nullable=False),
        sa.Column('acquired_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_locks_id'), 'file_locks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_file_locks_id'), table_name='file_locks')
    op.drop_table('file_locks')
