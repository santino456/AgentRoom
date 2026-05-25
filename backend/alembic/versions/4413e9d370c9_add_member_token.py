"""add_member_token

Revision ID: 4413e9d370c9
Revises: 0ba93f140032
Create Date: 2026-05-22 14:00:35.794532

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4413e9d370c9'
down_revision: Union[str, Sequence[str], None] = '0ba93f140032'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('members', sa.Column('token', sa.String(), nullable=True))
    op.create_index(op.f('ix_members_token'), 'members', ['token'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_members_token'), table_name='members')
    op.drop_column('members', 'token')
