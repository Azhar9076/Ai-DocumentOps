import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_YAML_PATH = BASE_DIR / "config" / "routing_thresholds.yaml"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DOCOPS_",
        extra="ignore",          # Ignores unrecognized env variables instead of crashing
        case_sensitive=False
    )

    # Core settings
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://docops:docops@localhost:5432/documentops"
    )
    storage_dir: Path = BASE_DIR / "storage"
    auto_approve_threshold: float = 0.90
    review_threshold: float = 0.70
    cors_origins: str = "*"

    # IBM watsonx.ai fields (Will read DOCOPS_WATSONX_API_KEY, etc.)
    watsonx_api_key: str = ""
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_project_id: str = ""


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)


def load_yaml_thresholds() -> None:
    if CONFIG_YAML_PATH.exists():
        try:
            data = yaml.safe_load(CONFIG_YAML_PATH.read_text(encoding="utf-8")) or {}
            rt = data.get("routing_thresholds", {})
            if "auto_approved_min" in rt:
                settings.auto_approve_threshold = float(rt["auto_approved_min"])
            if "needs_review_min" in rt:
                settings.review_threshold = float(rt["needs_review_min"])
        except Exception:
            pass


def save_routing_thresholds(auto_approved_min: float, needs_review_min: float) -> None:
    settings.auto_approve_threshold = round(float(auto_approved_min), 4)
    settings.review_threshold = round(float(needs_review_min), 4)
    try:
        CONFIG_YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
        content = {
            "routing_thresholds": {
                "auto_approved_min": settings.auto_approve_threshold,
                "needs_review_min": settings.review_threshold,
            }
        }
        CONFIG_YAML_PATH.write_text(yaml.safe_dump(content), encoding="utf-8")
    except Exception:
        pass


load_yaml_thresholds()