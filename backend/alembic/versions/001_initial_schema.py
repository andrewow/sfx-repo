"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("avatar_url", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )

    # Sounds table
    op.create_table(
        "sounds",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("drive_file_id", sa.Text, unique=True, nullable=False),
        sa.Column("duration_seconds", sa.Real),
        sa.Column("notes", sa.Text),
        sa.Column("is_new", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("drive_url", sa.Text),
        sa.Column("mime_type", sa.Text, server_default=sa.text("'audio/mpeg'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sounds_filename_trgm", "sounds", ["filename"], postgresql_using="gin", postgresql_ops={"filename": "gin_trgm_ops"})
    op.create_index("idx_sounds_is_new", "sounds", ["is_new"], postgresql_where=sa.text("is_new = true"))

    # Tags table
    op.create_table(
        "tags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, unique=True, nullable=False),
    )

    # Sound-Tags join table
    op.create_table(
        "sound_tags",
        sa.Column("sound_id", UUID(as_uuid=True), sa.ForeignKey("sounds.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sound_tags_tag", "sound_tags", ["tag_id"])
    op.create_index("idx_sound_tags_sound", "sound_tags", ["sound_id"])

    # Favorites table
    op.create_table(
        "favorites",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("sound_id", UUID(as_uuid=True), sa.ForeignKey("sounds.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_favorites_user", "favorites", ["user_id"])
    op.create_index("idx_favorites_sound", "favorites", ["sound_id"])


def downgrade() -> None:
    op.drop_table("favorites")
    op.drop_table("sound_tags")
    op.drop_table("tags")
    op.drop_table("sounds")
    op.drop_table("users")
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
