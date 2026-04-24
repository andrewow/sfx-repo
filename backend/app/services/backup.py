"""SFX Repository database backup.

Runs as a CLI (``python -m app.services.backup``) or is callable as a library
via :func:`run_backup` and :func:`get_last_backup`.

Pipeline: ``pg_dump`` against ``DATABASE_URL`` → gzip → upload to a Google
Drive Shared Drive folder via the existing service account. Drive is treated
as the authoritative record of "last backup"; there is no local metadata
file, so nothing is lost when the container is redeployed.
"""

import gzip
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _psql_url() -> str:
    """Convert the SQLAlchemy async URL to a libpq-compatible URL for pg_dump."""
    url = settings.database_url
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def _run_pg_dump(out_path: Path) -> None:
    """Stream pg_dump stdout into a gzip file. Raises on non-zero exit."""
    with gzip.open(out_path, "wb") as gz:
        proc = subprocess.run(
            ["pg_dump", "--no-owner", "--no-privileges", _psql_url()],
            stdout=gz,
            stderr=subprocess.PIPE,
            check=False,
        )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"pg_dump failed (exit {proc.returncode}): {err}")


def _drive_service():
    if not settings.google_service_account_json:
        return None
    info = json.loads(settings.google_service_account_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _upload_to_drive(local_path: Path) -> str:
    """Upload to the Shared Drive folder. Returns the Drive file id."""
    if not settings.backup_drive_folder_id:
        raise RuntimeError("BACKUP_DRIVE_FOLDER_ID not configured")
    service = _drive_service()
    if service is None:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not configured")
    media = MediaFileUpload(str(local_path), mimetype="application/gzip", resumable=True)
    body = {"name": local_path.name, "parents": [settings.backup_drive_folder_id]}
    # supportsAllDrives=True is required for Shared Drive folders; without it
    # the API returns "File not found" for the parent.
    result = (
        service.files()
        .create(body=body, media_body=media, fields="id,name", supportsAllDrives=True)
        .execute()
    )
    return result["id"]


def get_last_backup() -> dict | None:
    """Return the most recent backup file in the Drive folder, or None."""
    if not settings.backup_drive_folder_id:
        return None
    service = _drive_service()
    if service is None:
        return None
    try:
        result = (
            service.files()
            .list(
                q=f"'{settings.backup_drive_folder_id}' in parents and trashed=false",
                orderBy="createdTime desc",
                pageSize=1,
                fields="files(id,name,createdTime,size)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
    except Exception as e:
        logger.warning("Failed to list Drive backups: %s", e)
        return None
    files = result.get("files", [])
    if not files:
        return None
    f = files[0]
    return {
        "id": f["id"],
        "name": f["name"],
        "created_time": f["createdTime"],
        "size_bytes": int(f.get("size", 0)),
    }


def run_backup() -> dict:
    """Run the full backup pipeline. Returns a summary dict."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"sfx_backup_{ts}.sql.gz"
    backup_dir = Path(settings.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    local_path = backup_dir / backup_name

    logger.info("Starting backup: %s", backup_name)
    started_at = datetime.now(timezone.utc)

    _run_pg_dump(local_path)
    size_mb = local_path.stat().st_size / (1024 * 1024)
    logger.info("pg_dump complete: %s (%.2f MB)", local_path, size_mb)

    uploaded = False
    skip_reason: str | None = None
    drive_file_id: str | None = None

    if settings.backup_drive_folder_id and settings.google_service_account_json:
        drive_file_id = _upload_to_drive(local_path)
        uploaded = True
        logger.info("Uploaded to Drive: file_id=%s", drive_file_id)
    else:
        missing = []
        if not settings.backup_drive_folder_id:
            missing.append("BACKUP_DRIVE_FOLDER_ID")
        if not settings.google_service_account_json:
            missing.append("GOOGLE_SERVICE_ACCOUNT_JSON")
        skip_reason = (
            f"Skipped Drive upload (missing: {', '.join(missing)}). "
            f"Local backup remains at {local_path}"
        )
        logger.warning(skip_reason)

    # /tmp is ephemeral on Render but freeing the file still matters during
    # long-lived local dev and keeps disk usage bounded.
    if uploaded:
        try:
            local_path.unlink()
        except OSError:
            pass

    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    return {
        "name": backup_name,
        "size_mb": round(size_mb, 2),
        "elapsed_seconds": round(elapsed, 1),
        "uploaded": uploaded,
        "drive_file_id": drive_file_id,
        "skip_reason": skip_reason,
    }


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )


def main() -> int:
    _configure_logging()
    try:
        summary = run_backup()
        logger.info("Backup complete: %s", summary)
        return 0
    except Exception:
        logger.exception("Backup failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
