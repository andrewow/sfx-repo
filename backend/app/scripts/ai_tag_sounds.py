"""Batch script: use Gemini to suggest tags for untagged sounds.

Run from the backend directory:

    PYTHONPATH=. python -m app.scripts.ai_tag_sounds --limit 10
    PYTHONPATH=. python -m app.scripts.ai_tag_sounds --dry-run
    PYTHONPATH=. python -m app.scripts.ai_tag_sounds            # all untagged
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.database import async_session
from app.models import Sound, SoundTag, Tag
from app.services.ai_tagger import suggest_tags
from app.services.drive import stream_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ai_tag_sounds")


async def process_sound(session, sound: Sound, tag_map: dict[str, Tag], dry_run: bool) -> int:
    """Fetch audio, ask Gemini, persist tags. Returns number of tags applied."""
    logger.info(f"Processing: {sound.filename}")
    audio_stream = await asyncio.to_thread(stream_file, sound.drive_file_id)
    audio_bytes = audio_stream.read()
    if not audio_bytes:
        logger.warning(f"  empty audio stream for {sound.filename}; skipping")
        return 0

    existing = list(tag_map.keys())
    suggested = await suggest_tags(audio_bytes, sound.mime_type, existing)
    if not suggested:
        logger.warning(f"  no tags returned for {sound.filename}")
        return 0

    logger.info(f"  suggested: {suggested}")
    if dry_run:
        return len(suggested)

    for tag_name in suggested:
        tag = tag_map.get(tag_name)
        if tag is None:
            tag = Tag(name=tag_name)
            session.add(tag)
            await session.flush()
            tag_map[tag_name] = tag
        existing_link = await session.execute(
            select(SoundTag).where(SoundTag.sound_id == sound.id, SoundTag.tag_id == tag.id)
        )
        if existing_link.scalar_one_or_none():
            continue
        session.add(SoundTag(sound_id=sound.id, tag_id=tag.id, added_by=None))

    sound.ai_tagged = True
    await session.commit()
    return len(suggested)


async def run(limit: int | None, dry_run: bool) -> None:
    async with async_session() as session:
        tag_rows = (await session.execute(select(Tag))).scalars().all()
        tag_map: dict[str, Tag] = {t.name: t for t in tag_rows}
        logger.info(f"Loaded {len(tag_map)} existing tags")

        tagged_subq = select(SoundTag.sound_id).distinct()
        query = (
            select(Sound)
            .where(Sound.ai_tagged.is_(False))
            .where(~Sound.id.in_(tagged_subq))
            .order_by(Sound.filename)
        )
        if limit:
            query = query.limit(limit)

        candidates = (await session.execute(query)).scalars().all()
        logger.info(f"Found {len(candidates)} sounds to process (dry_run={dry_run})")

        processed = 0
        failed = 0
        for sound in candidates:
            try:
                applied = await process_sound(session, sound, tag_map, dry_run)
                if applied:
                    processed += 1
            except Exception as exc:
                failed += 1
                logger.exception(f"  failed on {sound.filename}: {exc}")
                await session.rollback()

        logger.info(f"Done. processed={processed} failed={failed} dry_run={dry_run}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AI tags for untagged sounds via Gemini.")
    parser.add_argument("--limit", type=int, default=None, help="Max number of sounds to process")
    parser.add_argument("--dry-run", action="store_true", help="Log suggestions without writing to DB")
    args = parser.parse_args()

    asyncio.run(run(args.limit, args.dry_run))


if __name__ == "__main__":
    main()
