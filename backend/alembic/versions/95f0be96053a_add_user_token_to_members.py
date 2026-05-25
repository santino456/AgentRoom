"""add_user_token_to_members

Revision ID: 95f0be96053a
Revises: 197e62352c22
Create Date: 2026-05-22 15:15:09.893419

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '95f0be96053a'
down_revision: Union[str, Sequence[str], None] = '197e62352c22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('members', sa.Column('user_token', sa.String(), nullable=True))
    op.create_index(op.f('ix_members_user_token'), 'members', ['user_token'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_members_user_token'), table_name='members')
    op.drop_column('members', 'user_token')
