import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@lru_cache(maxsize=1)
def get_settings():
    settings = {
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./auth.db"),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY", ""),
        "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM", "HS256"),
        "ACCESS_TOKEN_EXPIRE_MINUTES": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    }

    if not settings["JWT_SECRET_KEY"] or settings["JWT_SECRET_KEY"].lower() in {"replace_with_a_strong_random_secret", "change-me", "your-secret-key"}:
        raise RuntimeError("JWT_SECRET_KEY must be set to a strong random value in backend/.env")
    if settings["JWT_ALGORITHM"] not in {"HS256"}:
        raise RuntimeError("JWT_ALGORITHM must be HS256")

    return settings
