import asyncio

from app.config import settings
from app.models import SocialConnection, SocialPost
from app.providers.base import ProviderError, PublishResult
from app.providers.helpers import json_request
from app.security import decrypt_secret


class InstagramAdapter:
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        ig_user_id = connection.metadata_json.get("ig_user_id") or connection.external_account_id
        token = decrypt_secret(connection.access_token_encrypted)
        if not ig_user_id or not token:
            raise ProviderError("Instagram user ID and access token are required")
        if not post.media_url:
            raise ProviderError("Instagram publishing requires a public media URL")

        caption = post.body
        if post.hashtags:
            caption += "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
        media_type = str(post.provider_payload.get("media_type") or connection.metadata_json.get("media_type") or "IMAGE").upper()
        create_url = f"https://graph.facebook.com/{settings.meta_graph_version}/{ig_user_id}/media"
        data = {"caption": caption, "access_token": token}
        if media_type in {"REELS", "VIDEO"}:
            data.update({"media_type": "REELS", "video_url": post.media_url})
        else:
            data.update({"image_url": post.media_url})
        _, created = await json_request("POST", create_url, data=data)
        container_id = created.get("id")
        if not container_id:
            raise ProviderError("Instagram did not create a media container", response=created)

        if media_type in {"REELS", "VIDEO"}:
            status_url = f"https://graph.facebook.com/{settings.meta_graph_version}/{container_id}"
            for _ in range(20):
                await asyncio.sleep(3)
                _, state = await json_request(
                    "GET",
                    status_url,
                    params={"fields": "status_code", "access_token": token},
                )
                code = state.get("status_code")
                if code == "FINISHED":
                    break
                if code == "ERROR":
                    raise ProviderError("Instagram media processing failed", response=state)
            else:
                raise ProviderError("Instagram media is still processing", retryable=True)

        publish_url = f"https://graph.facebook.com/{settings.meta_graph_version}/{ig_user_id}/media_publish"
        _, published = await json_request(
            "POST",
            publish_url,
            data={"creation_id": container_id, "access_token": token},
        )
        external_id = str(published.get("id") or "")
        if not external_id:
            raise ProviderError("Instagram did not return a media ID", response=published)
        return PublishResult(external_id=external_id, raw={"container": created, "published": published})
