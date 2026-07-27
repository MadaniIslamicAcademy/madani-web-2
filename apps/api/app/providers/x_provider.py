from app.models import SocialConnection, SocialPost
from app.providers.base import ProviderError, PublishResult
from app.providers.helpers import json_request
from app.security import decrypt_secret


class XAdapter:
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        token = decrypt_secret(connection.access_token_encrypted)
        if not token:
            raise ProviderError("X user access token is required")
        text = post.body
        if post.hashtags:
            text += "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
        _, payload = await json_request(
            "POST",
            "https://api.x.com/2/tweets",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json_body={"text": text[:280]},
        )
        external_id = str((payload.get("data") or {}).get("id") or "")
        if not external_id:
            raise ProviderError("X did not return a post ID", response=payload)
        return PublishResult(external_id=external_id, url=f"https://x.com/i/web/status/{external_id}", raw=payload)
