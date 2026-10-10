from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings["ACCESS_TOKEN_EXPIRE_MINUTES"]))
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings["JWT_SECRET_KEY"], algorithm=settings["JWT_ALGORITHM"]) 


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings["JWT_SECRET_KEY"],
            algorithms=[settings["JWT_ALGORITHM"]],
            options={"require": ["sub", "exp", "iat"]},
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc


def hash_password_bcrypt(password: str) -> str:
    return get_password_hash(password)
