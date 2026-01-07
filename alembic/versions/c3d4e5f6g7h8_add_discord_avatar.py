"""add discord_avatar column

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-07 00:00:00.000000

Store Discord avatar hash to display user avatars in the web frontend.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('discord_avatar', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'discord_avatar')
