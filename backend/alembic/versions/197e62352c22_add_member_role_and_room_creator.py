"""add_member_role_and_room_creator

Revision ID: 197e62352c22
Revises: 4413e9d370c9
Create Date: 2026-05-22 14:56:08.480871

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '197e62352c22'
down_revision: Union[str, Sequence[str], None] = '4413e9d370c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('members', sa.Column('role', sa.String(), nullable=True))
    op.add_column('rooms', sa.Column('created_by_member_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('rooms', 'created_by_member_id')
    op.drop_column('members', 'role')
