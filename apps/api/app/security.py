from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
import base64
import hashlib
import hmac
import os

import jwt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Request, Response, status
try:
    from pwdlib import PasswordHash
except ImportError:
    PasswordHash = None

from app.config import settings

password_hash = PasswordHash.recommended() if PasswordHash else None
ALGORITHM = "HS256"
ACCESS_COOKIE = "madani_access"
CSRF_COOKIE = "madani_csrf"


def hash_password(password: str) -> str:
    if password_hash:
        return password_hash.hash(password)
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return f"pbkdf2_sha256${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, hashed: str) -> bool:
    if hashed.startswith("pbkdf2_sha256$"):
        _, salt_text, digest_text = hashed.split("$", 2)
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
        return hmac.compare_digest(actual, expected)
    if not password_hash:
        return False
    return password_hash.verify(password, hashed)


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc


def set_auth_cookies(response: Response, token: str) -> str:
    csrf = token_urlsafe(32)
    common = {
        "secure": settings.cookie_secure,
        "samesite": "none" if settings.cookie_secure else "lax",
        "path": "/",
    }
    response.set_cookie(
        ACCESS_COOKIE,
        token,
        httponly=True,
        max_age=settings.access_token_minutes * 60,
        **common,
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        httponly=False,
        max_age=settings.access_token_minutes * 60,
        **common,
    )
    return csrf


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


def require_csrf(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or cookie != header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def _fernet() -> Fernet:
    key = settings.token_encryption_key.strip()
    if not key:
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest()).decode()
    try:
        return Fernet(key.encode())
    except ValueError as exc:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY must be a valid Fernet key") from exc


def encrypt_secret(value: str) -> str:
    if not value:
        return ""
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Stored provider token could not be decrypted") from exc
