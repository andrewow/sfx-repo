"""One-time import script to seed the database from the Google Sheet XLSX export."""

import asyncio
import logging
import re
import sys
from pathlib import Path

import openpyxl
from sqlalchemy import select

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.database import async_session, engine
from app.models import Base, Favorite, Sound, SoundTag, Tag, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Map legacy initials to placeholder emails
INITIALS_MAP = {
    "$AF": "af@haikugames.com",
    "$RS": "rs@haikugames.com",
}

DRIVE_ID_REGEX = re.compile(r"/file/d/([^/]+)/")
DURATION_MIN_REGEX = re.compile(r"([\d.]+)\s*MIN", re.IGNORECASE)


def parse_duration(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    match = DURATION_MIN_REGEX.match(s)
    if match:
        return float(match.group(1)) * 60.0
    return None


def extract_drive_id(url: str) -> str | None:
    if not url:
        return None
    match = DRIVE_ID_REGEX.search(url)
    return match.group(1) if match else None


def get_mime_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".wav"):
        return "audio/wav"
    return "audio/mpeg"


async def import_xlsx(xlsx_path: str):
    logger.info(f"Loading workbook: {xlsx_path}")
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    # Collect all rows
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=False):
        filename = row[0].value
        if not filename:
            continue
        # Skip non-audio files (.aup3)
        if filename.lower().endswith(".aup3"):
            logger.info(f"Skipping Audacity project file: {filename}")
            continue

        tags_str = row[1].value
        duration = parse_duration(row[2].value)
        link = str(row[3].value) if row[3].value else None
        fav_count = row[5].value
        initials_str = str(row[6].value).strip() if row[6].value else None
        notes = str(row[7].value).strip() if row[7].value else None

        drive_id = extract_drive_id(link) if link else None
        if not drive_id:
            logger.warning(f"No Drive ID found for {filename}, skipping")
            continue

        # Parse tags
        tag_list = []
        if tags_str:
            tag_list = [t.strip().lower() for t in str(tags_str).split(",") if t.strip()]

        # Parse initials for favorites
        fav_initials = []
        if initials_str and initials_str != "None":
            fav_initials = [i.strip() for i in initials_str.split(",") if i.strip().startswith("$")]

        has_tags = len(tag_list) > 0

        rows.append({
            "filename": filename,
            "drive_file_id": drive_id,
            "duration_seconds": duration,
            "notes": notes if notes and notes != "None" else None,
            "drive_url": link,
            "mime_type": get_mime_type(filename),
            "is_new": not has_tags,
            "tags": tag_list,
            "fav_initials": fav_initials,
        })

    logger.info(f"Parsed {len(rows)} sound entries")

    # Collect all unique tags
    all_tags = set()
    for r in rows:
        all_tags.update(r["tags"])
    logger.info(f"Found {len(all_tags)} unique tags")

    # Collect all unique initials that need user records
    all_initials = set()
    for r in rows:
        all_initials.update(r["fav_initials"])
    logger.info(f"Found initials: {all_initials}")

    async with async_session() as session:
        # Check if data already imported
        result = await session.execute(select(Sound).limit(1))
        if result.scalar_one_or_none():
            logger.warning("Database already has sound data. Skipping import to avoid duplicates.")
            logger.warning("To re-import, truncate the sounds table first.")
            return

        # Create placeholder users for legacy favorites
        user_map = {}  # initials -> user
        for initials, email in INITIALS_MAP.items():
            if initials in all_initials:
                user = User(email=email, display_name=initials.replace("$", ""))
                session.add(user)
                user_map[initials] = user
        await session.flush()

        # Create all tags
        tag_map = {}  # name -> Tag
        for tag_name in all_tags:
            tag = Tag(name=tag_name)
            session.add(tag)
            tag_map[tag_name] = tag
        await session.flush()

        # Create sounds, sound_tags, and favorites
        sounds_created = 0
        tags_created = 0
        favs_created = 0

        for r in rows:
            sound = Sound(
                filename=r["filename"],
                drive_file_id=r["drive_file_id"],
                duration_seconds=r["duration_seconds"],
                notes=r["notes"],
                is_new=r["is_new"],
                drive_url=r["drive_url"],
                mime_type=r["mime_type"],
            )
            session.add(sound)
            await session.flush()
            sounds_created += 1

            # Create sound_tags
            for tag_name in r["tags"]:
                tag = tag_map[tag_name]
                sound_tag = SoundTag(sound_id=sound.id, tag_id=tag.id)
                session.add(sound_tag)
                tags_created += 1

            # Create favorites from legacy initials
            for initials in r["fav_initials"]:
                if initials in user_map:
                    fav = Favorite(user_id=user_map[initials].id, sound_id=sound.id)
                    session.add(fav)
                    favs_created += 1

        await session.commit()

        logger.info(f"Import complete:")
        logger.info(f"  Sounds: {sounds_created}")
        logger.info(f"  Tags: {len(tag_map)}")
        logger.info(f"  Sound-tag associations: {tags_created}")
        logger.info(f"  Legacy favorites: {favs_created}")
        logger.info(f"  Legacy users: {len(user_map)}")


def main():
    xlsx_path = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent.parent.parent / "Sound Effects Repository.xlsx")
    asyncio.run(import_xlsx(xlsx_path))


if __name__ == "__main__":
    main()
