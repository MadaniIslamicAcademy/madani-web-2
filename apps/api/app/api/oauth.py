from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config import settings
from app.dependencies import AdminUser, CsrfProtected, DbSession
from app.enums import SocialProvider
from app.models import SocialConnection
from app.security import encrypt_secret

router = APIRouter(prefix="/oauth", tags=["OAuth"])

PROVIDERS = {
    "meta": {
        "provider": SocialProvider.FACEBOOK,
        "authorize": f"https://www.facebook.com/{settings.meta_graph_version}/dialog/oauth",
        "token": f"https://graph.facebook.com/{settings.meta_graph_version}/oauth/access_token",
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "redirect_uri": settings.meta_redirect_uri,
        "scope": "pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish,whatsapp_business_messaging",
    },
    "linkedin": {
        "provider": SocialProvider.LINKEDIN,
        "authorize": "https://www.linkedin.com/oauth/v2/authorization",
        "token": "https://www.linkedin.com/oauth/v2/accessToken",
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
        "redirect_uri": settings.linkedin_redirect_uri,
        "scope": "openid profile w_organization_social",
    },
    "google": {
        "provider": SocialProvider.YOUTUBE,
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "scope": "https://www.googleapis.com/auth/youtube.upload",
    },
    "tiktok": {
        "provider": SocialProvider.TIKTOK,
        "authorize": "https://www.tiktok.com/v2/auth/authorize/",
        "token": "https://open.tiktokapis.com/v2/oauth/token/",
        "client_id": settings.tiktok_client_key,
        "client_secret": settings.tiktok_client_secret,
        "redirect_uri": settings.tiktok_redirect_uri,
        "scope": "user.info.basic,video.publish,video.upload",
    },
}


def make_state(provider: str, user_id: str, external_account_id: str, display_name: str) -> str:
    return jwt.encode(
        {
            "provider": provider,
            "sub": user_id,
            "external_account_id": external_account_id,
            "display_name": display_name,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        },
        settings.secret_key,
        algorithm="HS256",
    )


@router.get("/{provider}/start")
def oauth_start(
    provider: str,
    user: AdminUser,
    csrf: CsrfProtected,
    external_account_id: str = Query(min_length=1),
    display_name: str = Query(min_length=2),
) -> dict[str, str]:
    config = PROVIDERS.get(provider)
    if not config or not config["client_id"]:
        raise HTTPException(status_code=400, detail="Provider OAuth is not configured")
    state = make_state(provider, user.id, external_account_id, display_name)
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
    }
    if provider == "google":
        params.update({"access_type": "offline", "prompt": "consent"})
    return {"authorization_url": f"{config['authorize']}?{urlencode(params)}"}


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str, db: DbSession) -> RedirectResponse:
    config = PROVIDERS.get(provider)
    if not config:
        raise HTTPException(status_code=404, detail="Unknown provider")
    try:
        state_data = jwt.decode(state, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
    if state_data.get("provider") != provider:
        raise HTTPException(status_code=400, detail="OAuth provider mismatch")
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(config["token"], data=data, headers={"Accept": "application/json"})
    try:
        token_data = response.json()
    except ValueError:
        token_data = {"error": response.text}
    if response.status_code >= 400 or not token_data.get("access_token"):
        raise HTTPException(status_code=502, detail={"oauth_error": token_data})
    connection = SocialConnection(
        provider=config["provider"],
        display_name=state_data["display_name"],
        external_account_id=state_data["external_account_id"],
        access_token_encrypted=encrypt_secret(token_data["access_token"]),
        refresh_token_encrypted=encrypt_secret(token_data.get("refresh_token", "")),
        token_expires_at=(datetime.now(timezone.utc) + timedelta(seconds=int(token_data.get("expires_in", 0)))) if token_data.get("expires_in") else None,
        metadata_json={"oauth_provider": provider},
        connected_by_id=state_data["sub"],
    )
    db.add(connection)
    db.commit()
    return RedirectResponse(f"{settings.frontend_url.split(',')[0]}/connections?connected={provider}")
