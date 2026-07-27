from app.models import SocialConnection, SocialPost
from app.providers.base import ProviderError, PublishResult
from app.providers.helpers import json_request
from app.security import decrypt_secret


class TikTokAdapter:
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        token = decrypt_secret(connection.access_token_encrypted)
        if not token:
            raise ProviderError("TikTok access token is required")
        privacy = post.provider_payload.get("privacy_level") or connection.metadata_json.get("privacy_level") or "SELF_ONLY"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}
        caption = post.body
        if post.hashtags:
            caption += "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
        image_urls = post.provider_payload.get("photo_images") or []
        if image_urls:
            body = {
                "media_type": "PHOTO",
                "post_mode": "DIRECT_POST",
                "post_info": {
                    "title": post.title[:90],
                    "description": caption[:4000],
                    "privacy_level": privacy,
                    "disable_comment": bool(post.provider_payload.get("disable_comment", False)),
                    "auto_add_music": bool(post.provider_payload.get("auto_add_music", False)),
                    "brand_content_toggle": False,
                    "brand_organic_toggle": bool(post.provider_payload.get("brand_organic_toggle", True)),
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "photo_images": image_urls,
                    "photo_cover_index": int(post.provider_payload.get("photo_cover_index", 0)),
                },
            }
            _, payload = await json_request(
                "POST",
                "https://open.tiktokapis.com/v2/post/publish/content/init/",
                headers=headers,
                json_body=body,
            )
        else:
            if not post.media_url:
                raise ProviderError("TikTok publishing requires a public video URL or photo_images")
            body = {
                "post_info": {
                    "title": caption[:2200],
                    "privacy_level": privacy,
                    "disable_duet": bool(post.provider_payload.get("disable_duet", False)),
                    "disable_comment": bool(post.provider_payload.get("disable_comment", False)),
                    "disable_stitch": bool(post.provider_payload.get("disable_stitch", False)),
                    "brand_content_toggle": False,
                    "brand_organic_toggle": bool(post.provider_payload.get("brand_organic_toggle", True)),
                    "is_aigc": bool(post.provider_payload.get("is_aigc", False)),
                },
                "source_info": {"source": "PULL_FROM_URL", "video_url": post.media_url},
            }
            _, payload = await json_request(
                "POST",
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                headers=headers,
                json_body=body,
            )
        error = payload.get("error") or {}
        if error.get("code") not in {None, "ok"}:
            raise ProviderError(error.get("message") or "TikTok rejected the post", response=payload)
        publish_id = str((payload.get("data") or {}).get("publish_id") or "")
        if not publish_id:
            raise ProviderError("TikTok did not return a publish ID", response=payload)
        return PublishResult(external_id=publish_id, raw=payload)
