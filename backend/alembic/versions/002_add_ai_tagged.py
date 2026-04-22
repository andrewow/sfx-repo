"""Add ai_tagged column to sounds

Revision ID: 002
Revises: 001
Create Date: 2026-04-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sounds",
        sa.Column("ai_tagged", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.create_index(
        "idx_sounds_ai_tagged",
        "sounds",
        ["ai_tagged"],
        postgresql_where=sa.text("ai_tagged = true"),
    )


def downgrade() -> None:
    op.drop_index("idx_sounds_ai_tagged", table_name="sounds")
    op.drop_column("sounds", "ai_tagged")
