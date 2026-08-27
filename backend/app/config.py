from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DOCOPS_")

    database_url: str = "postgresql://neondb_owner:npg_dnUsS0M5ezRC@ep-restless-sun-aykfnoxu-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    storage_dir: Path = BASE_DIR / "storage"
    auto_approve_threshold: float = 0.90
    review_threshold: float = 0.70
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # IBM Watson Credentials
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_api_key: str = "StxByWjg3HI_AbnKMcq2ag6ONNIQUqr_0vrQPzPtfYNs"
    watsonx_project_id: str = "1c8f21bf-3889-496d-aa61-2e60b5e3af1c"
    watsonx_model_id: str = "ibm/granite-4-h-small"
    watsonx_deployment_id: str = ""


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
