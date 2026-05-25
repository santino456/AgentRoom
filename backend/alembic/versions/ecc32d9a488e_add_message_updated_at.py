"""add message updated_at

Revision ID: ecc32d9a488e
Revises: 1b7a7af44b79
Create Date: 2026-05-21 19:37:15.866688

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ecc32d9a488e'
down_revision: Union[str, Sequence[str], None] = '1b7a7af44b79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'updated_at')
