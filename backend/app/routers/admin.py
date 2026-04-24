import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.config import settings
from app.models import User
from app.services.backup import get_last_backup

router = APIRouter(prefix="/api/admin", tags=["admin"])

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


def _tail_log(path: Path, max_lines: int = 200) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            read = min(size, 64 * 1024)
            fh.seek(size - read)
            data = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return ""
    lines = data.splitlines()
    return "\n".join(lines[-max_lines:])


@router.post("/backup", status_code=202)
async def trigger_backup(user: User = Depends(get_current_user)):
    """Spawn the backup as a detached subprocess and return immediately.

    The child process is started with ``start_new_session=True`` so it outlives
    a worker restart or request timeout. Stdout/stderr are redirected to a log
    file that the status endpoint can tail.
    """
    log_path = Path(settings.backup_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "w")  # noqa: SIM115 — intentionally left open for the child
    try:
        subprocess.Popen(
            [sys.executable, "-m", "app.services.backup"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
            cwd=str(BACKEND_ROOT),
        )
    finally:
        # The child has inherited the fd; we can close ours.
        log_file.close()
    return {"status": "started", "triggered_by": user.email}


@router.get("/backup/status")
async def backup_status(user: User = Depends(get_current_user)):
    last = get_last_backup()
    days_ago: float | None = None
    is_stale = False
    if last:
        created = datetime.fromisoformat(last["created_time"].replace("Z", "+00:00"))
        days_ago = (datetime.now(timezone.utc) - created).total_seconds() / 86400.0
        is_stale = days_ago > settings.backup_stale_days
    else:
        # No backup found in Drive — treat as stale so the UI flags it red.
        is_stale = True
    return {
        "last_backup": last,
        "days_ago": days_ago,
        "is_stale": is_stale,
        "stale_threshold_days": settings.backup_stale_days,
        "drive_folder_configured": bool(settings.backup_drive_folder_id),
        "log_tail": _tail_log(Path(settings.backup_log_path)),
    }
