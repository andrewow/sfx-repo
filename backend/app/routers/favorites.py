from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Favorite, Sound, User

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("/{sound_id}", status_code=201)
async def add_favorite(
    sound_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Verify sound exists
    result = await db.execute(select(Sound).where(Sound.id == sound_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sound not found")

    # Check if already favorited
    result = await db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.sound_id == sound_id))
    if result.scalar_one_or_none():
        return {"detail": "Already favorited"}

    favorite = Favorite(user_id=user.id, sound_id=sound_id)
    db.add(favorite)
    await db.commit()
    return {"detail": "Favorited"}


@router.delete("/{sound_id}", status_code=204)
async def remove_favorite(
    sound_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.sound_id == sound_id))
    favorite = result.scalar_one_or_none()
    if favorite:
        await db.delete(favorite)
        await db.commit()
