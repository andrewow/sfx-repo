from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/sfx_repository"

    @model_validator(mode="after")
    def fix_database_url(self):
        url = self.database_url
        if url.startswith("postgres://"):
            self.database_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            self.database_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self
    google_client_id: str = ""
    google_client_secret: str = ""
    google_service_account_json: str = ""
    session_secret_key: str = "change-me-in-production"
    drive_folder_id: str = ""
    allowed_domain: str = "haikugames.com"
    ingestion_interval_seconds: int = 900  # 15 minutes
    gemini_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
