from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import SoundTag, Tag, User
from app.schemas import TagWithCount

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagWithCount])
async def list_tags(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(Tag.name, func.count(SoundTag.sound_id).label("count"))
        .outerjoin(SoundTag, Tag.id == SoundTag.tag_id)
        .group_by(Tag.id, Tag.name)
        .order_by(func.count(SoundTag.sound_id).desc())
    )

    if q:
        query = query.where(func.lower(Tag.name).like(f"{q.lower()}%"))

    result = await db.execute(query)
    rows = result.all()
    return [TagWithCount(name=row.name, count=row.count) for row in rows]
