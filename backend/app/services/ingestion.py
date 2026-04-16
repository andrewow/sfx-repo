import asyncio
import logging

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models import Sound

logger = logging.getLogger(__name__)


async def run_ingestion() -> int:
    if not settings.google_service_account_json or not settings.drive_folder_id:
        logger.warning("Drive credentials or folder ID not configured, skipping ingestion")
        return 0

    from app.services.drive import list_folder_files

    drive_files = await asyncio.to_thread(list_folder_files, settings.drive_folder_id)

    async with async_session() as session:
        result = await session.execute(select(Sound.drive_file_id))
        existing_ids = {row[0] for row in result.all()}

    new_files = [f for f in drive_files if f["id"] not in existing_ids]

    if not new_files:
        return 0

    async with async_session() as session:
        for f in new_files:
            mime = f.get("mimeType", "audio/mpeg")
            if "wav" in mime:
                mime_type = "audio/wav"
            else:
                mime_type = "audio/mpeg"

            sound = Sound(
                filename=f["name"],
                drive_file_id=f["id"],
                mime_type=mime_type,
                is_new=True,
                drive_url=f"https://drive.google.com/file/d/{f['id']}/view",
            )
            session.add(sound)
        await session.commit()

    logger.info(f"Ingested {len(new_files)} new sound files from Google Drive")
    return len(new_files)


async def ingestion_loop():
    while True:
        try:
            count = await run_ingestion()
            if count:
                logger.info(f"Ingestion cycle complete: {count} new files")
        except Exception:
            logger.exception("Error during ingestion cycle")
        await asyncio.sleep(settings.ingestion_interval_seconds)
