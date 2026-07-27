from app.config import settings
from app.models import SocialConnection, SocialPost
from app.providers.base import ProviderError, PublishResult
from app.providers.helpers import json_request
from app.security import decrypt_secret


class FacebookAdapter:
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        page_id = connection.metadata_json.get("page_id") or connection.external_account_id
        token = decrypt_secret(connection.access_token_encrypted)
        if not page_id or not token:
            raise ProviderError("Facebook Page ID and access token are required")
        message = post.body
        if post.hashtags:
            message += "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
        if post.media_url:
            endpoint = f"https://graph.facebook.com/{settings.meta_graph_version}/{page_id}/photos"
            data = {"url": post.media_url, "caption": message, "access_token": token}
        else:
            endpoint = f"https://graph.facebook.com/{settings.meta_graph_version}/{page_id}/feed"
            data = {"message": message, "access_token": token}
        _, payload = await json_request("POST", endpoint, data=data)
        external_id = str(payload.get("post_id") or payload.get("id") or "")
        if not external_id:
            raise ProviderError("Facebook did not return a post ID", response=payload)
        return PublishResult(external_id=external_id, raw=payload)
