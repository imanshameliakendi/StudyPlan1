import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")


def _get(name: str, default: str) -> str:
    return os.getenv(name, default)


class Settings:
    APP_NAME = _get("APP_NAME", "StudyPlan")
    DATABASE_URL = _get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'storage' / 'studyplan.db'}")
    ADMIN_EMAIL = _get("ADMIN_EMAIL", "").strip().lower()
    ADMIN_PASSWORD = _get("ADMIN_PASSWORD", "")
    UPLOAD_DIR = Path(_get("UPLOAD_DIR", str(BASE_DIR / 'storage' / 'uploads'))).resolve()
    MAX_UPLOAD_SIZE_MB = int(_get("MAX_UPLOAD_SIZE_MB", "20"))
    TIMEZONE = _get("TIMEZONE", "UTC")
    CORS_ORIGINS = [
        origin.strip()
        for origin in _get(
            "CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501"
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
