from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/sfx_repository"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_service_account_json: str = ""
    session_secret_key: str = "change-me-in-production"
    drive_folder_id: str = ""
    frontend_url: str = "http://localhost:5173"
    allowed_domain: str = "haikugames.com"
    ingestion_interval_seconds: int = 900  # 15 minutes

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
