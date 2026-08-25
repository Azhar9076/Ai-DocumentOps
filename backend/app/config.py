from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DOCOPS_")

    database_url: str = "postgresql+psycopg2://docops:docops@localhost:5432/documentops"
    storage_dir: Path = BASE_DIR / "storage"
    auto_approve_threshold: float = 0.90
    review_threshold: float = 0.70
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
