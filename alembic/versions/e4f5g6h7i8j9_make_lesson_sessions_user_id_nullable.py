"""make lesson_sessions.user_id nullable

Revision ID: e4f5g6h7i8j9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-11 12:30:00.000000

Allow anonymous lesson sessions by making user_id nullable.
Anonymous sessions can later be claimed when user authenticates.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5g6h7i8j9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make user_id nullable to support anonymous sessions
    op.alter_column('lesson_sessions', 'user_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    # Note: This will fail if there are NULL values in user_id
    op.alter_column('lesson_sessions', 'user_id',
                    existing_type=sa.Integer(),
                    nullable=False)
