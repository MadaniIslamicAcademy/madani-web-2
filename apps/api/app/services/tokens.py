from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import SocialProvider
from app.models import SocialConnection
from app.security import decrypt_secret, encrypt_secret


async def refresh_connection_if_needed(db: Session, connection: SocialConnection) -> SocialConnection:
    if not connection.token_expires_at:
        return connection
    if connection.token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        return connection
    refresh_token = decrypt_secret(connection.refresh_token_encrypted)
    if not refresh_token:
        return connection
    oauth_provider = connection.metadata_json.get("oauth_provider")
    endpoint = ""
    data: dict[str, str] = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    headers: dict[str, str] = {"Accept": "application/json"}
    if oauth_provider == "google" or connection.provider == SocialProvider.YOUTUBE:
        endpoint = "https://oauth2.googleapis.com/token"
        data.update({"client_id": settings.google_client_id, "client_secret": settings.google_client_secret})
    elif oauth_provider == "linkedin" or connection.provider == SocialProvider.LINKEDIN:
        endpoint = "https://www.linkedin.com/oauth/v2/accessToken"
        data.update({"client_id": settings.linkedin_client_id, "client_secret": settings.linkedin_client_secret})
    elif oauth_provider == "tiktok" or connection.provider == SocialProvider.TIKTOK:
        endpoint = "https://open.tiktokapis.com/v2/oauth/token/"
        data.update({"client_key": settings.tiktok_client_key, "client_secret": settings.tiktok_client_secret})
    else:
        return connection
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(endpoint, data=data, headers=headers)
    if response.status_code >= 400:
        return connection
    payload = response.json()
    new_access = payload.get("access_token")
    if not new_access:
        return connection
    connection.access_token_encrypted = encrypt_secret(new_access)
    if payload.get("refresh_token"):
        connection.refresh_token_encrypted = encrypt_secret(payload["refresh_token"])
    if payload.get("expires_in"):
        connection.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(payload["expires_in"]))
    db.commit()
    db.refresh(connection)
    return connection
