import io
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _get_credentials():
    creds_json = json.loads(settings.google_service_account_json)
    return service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)


def get_drive_service():
    return build("drive", "v3", credentials=_get_credentials())


def stream_file(file_id: str) -> io.BytesIO:
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    stream = io.BytesIO()
    downloader = MediaIoBaseDownload(stream, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    stream.seek(0)
    return stream


def list_folder_files(folder_id: str) -> list[dict]:
    service = get_drive_service()
    results = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed=false and (mimeType='audio/mpeg' or mimeType='audio/wav' or mimeType='audio/x-wav')"
    while True:
        resp = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results
