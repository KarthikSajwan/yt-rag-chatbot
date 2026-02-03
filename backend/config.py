"""Application configuration from environment."""
from pathlib import Path

from pydantic_settings import BaseSettings

# Load .env from project root (parent of backend/) so it works when run from backend/
_env_path = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Settings loaded from environment."""

    openai_api_key: str = ""
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite:///./yt_rag.db"
    stores_path: str = "./data/stores"

    class Config:
        env_file = _env_path
        extra = "ignore"


def get_stores_dir() -> Path:
    """Return path to FAISS stores directory; create if needed."""
    path = Path(Settings().stores_path)
    path.mkdir(parents=True, exist_ok=True)
    return path
