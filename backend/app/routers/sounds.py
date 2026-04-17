import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Favorite, Sound, SoundTag, Tag, User
from app.schemas import AddTagRequest, SoundListResponse, SoundOut, TagOut, UpdateSoundRequest

router = APIRouter(prefix="/api/sounds", tags=["sounds"])


def _sound_to_out(sound: Sound, user_id: UUID) -> SoundOut:
    fav_user_ids = {f.user_id for f in sound.favorites}
    return SoundOut(
        id=sound.id,
        filename=sound.filename,
        duration_seconds=sound.duration_seconds,
        notes=sound.notes,
        is_new=sound.is_new,
        mime_type=sound.mime_type,
        tags=[TagOut(id=st.tag.id, name=st.tag.name) for st in sound.tags],
        is_favorited=user_id in fav_user_ids,
        created_at=sound.created_at,
    )


@router.get("", response_model=SoundListResponse)
async def list_sounds(
    q: str | None = None,
    tags: str | None = None,
    is_new: bool | None = None,
    favorites_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort: str = Query("filename", pattern="^(filename|duration_seconds|created_at)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Base query
    query = select(Sound).options(selectinload(Sound.tags).selectinload(SoundTag.tag), selectinload(Sound.favorites))

    # Search by filename or tags (each term must match via filename or tag)
    if q:
        terms = [t.strip().lower() for t in q.replace(",", " ").split() if t.strip()]
        for term in terms:
            search_term = f"%{term}%"
            tag_sound_ids = select(SoundTag.sound_id).join(Tag).where(func.lower(Tag.name).like(search_term))
            query = query.where((func.lower(Sound.filename).like(search_term)) | (Sound.id.in_(tag_sound_ids)))

    # Filter by specific tags (AND logic)
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        for tag_name in tag_list:
            tag_subq = select(SoundTag.sound_id).join(Tag).where(func.lower(Tag.name) == tag_name)
            query = query.where(Sound.id.in_(tag_subq))

    # Filter by is_new
    if is_new is not None:
        query = query.where(Sound.is_new == is_new)

    # Filter by favorites
    if favorites_only:
        fav_subq = select(Favorite.sound_id).where(Favorite.user_id == user.id)
        query = query.where(Sound.id.in_(fav_subq))

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    sort_col = getattr(Sound, sort)
    if order == "desc":
        query = query.order_by(sort_col.desc().nulls_last())
    else:
        query = query.order_by(sort_col.asc().nulls_last())

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    sounds = result.unique().scalars().all()

    return SoundListResponse(
        items=[_sound_to_out(s, user.id) for s in sounds],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{sound_id}", response_model=SoundOut)
async def get_sound(
    sound_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Sound)
        .options(selectinload(Sound.tags).selectinload(SoundTag.tag), selectinload(Sound.favorites))
        .where(Sound.id == sound_id)
    )
    sound = result.unique().scalar_one_or_none()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")
    return _sound_to_out(sound, user.id)


@router.get("/{sound_id}/audio")
async def stream_audio(
    sound_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sound).where(Sound.id == sound_id))
    sound = result.scalar_one_or_none()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")

    from app.services.drive import stream_file

    stream = await asyncio.to_thread(stream_file, sound.drive_file_id)

    return StreamingResponse(
        stream,
        media_type=sound.mime_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.patch("/{sound_id}", response_model=SoundOut)
async def update_sound(
    sound_id: UUID,
    body: UpdateSoundRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Sound)
        .options(selectinload(Sound.tags).selectinload(SoundTag.tag), selectinload(Sound.favorites))
        .where(Sound.id == sound_id)
    )
    sound = result.unique().scalar_one_or_none()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")

    if body.notes is not None:
        sound.notes = body.notes
    if body.is_new is not None:
        sound.is_new = body.is_new

    await db.commit()
    await db.refresh(sound, ["tags", "favorites"])
    return _sound_to_out(sound, user.id)


@router.post("/{sound_id}/tags", response_model=SoundOut)
async def add_tag(
    sound_id: UUID,
    body: AddTagRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sound).where(Sound.id == sound_id))
    sound = result.scalar_one_or_none()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")

    tag_name = body.tag.strip().lower()
    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    # Get or create tag
    result = await db.execute(select(Tag).where(Tag.name == tag_name))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        await db.flush()

    # Check if already tagged
    result = await db.execute(select(SoundTag).where(SoundTag.sound_id == sound_id, SoundTag.tag_id == tag.id))
    if result.scalar_one_or_none():
        pass  # Already tagged, no-op
    else:
        sound_tag = SoundTag(sound_id=sound_id, tag_id=tag.id, added_by=user.id)
        db.add(sound_tag)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Sound)
        .options(selectinload(Sound.tags).selectinload(SoundTag.tag), selectinload(Sound.favorites))
        .where(Sound.id == sound_id)
    )
    sound = result.unique().scalar_one_or_none()
    return _sound_to_out(sound, user.id)


@router.delete("/{sound_id}/tags/{tag_name}", response_model=SoundOut)
async def remove_tag(
    sound_id: UUID,
    tag_name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Tag).where(Tag.name == tag_name.strip().lower()))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    result = await db.execute(select(SoundTag).where(SoundTag.sound_id == sound_id, SoundTag.tag_id == tag.id))
    sound_tag = result.scalar_one_or_none()
    if sound_tag:
        await db.delete(sound_tag)
        await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Sound)
        .options(selectinload(Sound.tags).selectinload(SoundTag.tag), selectinload(Sound.favorites))
        .where(Sound.id == sound_id)
    )
    sound = result.unique().scalar_one_or_none()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")
    return _sound_to_out(sound, user.id)
