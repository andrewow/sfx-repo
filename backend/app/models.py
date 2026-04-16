import uuid
from datetime import datetime, timezone

from sqlalchemy import REAL, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Sound(Base):
    __tablename__ = "sounds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    drive_file_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(REAL)
    notes: Mapped[str | None] = mapped_column(Text)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    drive_url: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(Text, default="audio/mpeg")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tags: Mapped[list["SoundTag"]] = relationship(back_populates="sound", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="sound", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    sound_tags: Mapped[list["SoundTag"]] = relationship(back_populates="tag", cascade="all, delete-orphan")


class SoundTag(Base):
    __tablename__ = "sound_tags"

    sound_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sounds.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    added_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sound: Mapped["Sound"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="sound_tags")


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    sound_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sounds.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="favorites")
    sound: Mapped["Sound"] = relationship(back_populates="favorites")
