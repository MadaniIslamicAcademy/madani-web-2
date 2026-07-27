from app.config import settings
from app.models import SocialConnection, SocialPost
from app.providers.base import ProviderError, PublishResult
from app.providers.helpers import json_request
from app.security import decrypt_secret


class LinkedInAdapter:
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        token = decrypt_secret(connection.access_token_encrypted)
        author = connection.metadata_json.get("author_urn") or connection.external_account_id
        if not token or not author:
            raise ProviderError("LinkedIn token and author URN are required")
        commentary = post.body
        if post.hashtags:
            commentary += "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
        body = {
            "author": author,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if post.media_url and post.provider_payload.get("article_title"):
            body["content"] = {
                "article": {
                    "source": post.media_url,
                    "title": post.provider_payload.get("article_title") or post.title,
                    "description": post.provider_payload.get("article_description") or "",
                }
            }
        response, payload = await json_request(
            "POST",
            "https://api.linkedin.com/rest/posts",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
                "Linkedin-Version": settings.linkedin_version,
            },
            json_body=body,
        )
        external_id = response.headers.get("x-restli-id", "")
        if not external_id:
            raise ProviderError("LinkedIn did not return a post ID", response=payload)
        return PublishResult(external_id=external_id, raw=payload)
