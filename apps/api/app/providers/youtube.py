import os
import tempfile
from pathlib import Path

import httpx

from app.models import SocialConnection, SocialPost
from app.providers.base import ProviderError, PublishResult
from app.security import decrypt_secret


class YouTubeAdapter:
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        token = decrypt_secret(connection.access_token_encrypted)
        if not token:
            raise ProviderError("YouTube access token is required")
        if not post.media_url:
            raise ProviderError("YouTube publishing requires a video media URL")
        metadata = connection.metadata_json
        privacy = post.provider_payload.get("privacy_status") or metadata.get("privacy_status") or "private"
        category = post.provider_payload.get("category_id") or metadata.get("category_id") or "27"
        description = post.body
        if post.hashtags:
            description += "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)

        temp_path = ""
        try:
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                media_response = await client.get(post.media_url)
                media_response.raise_for_status()
                content_type = media_response.headers.get("content-type", "video/mp4").split(";")[0]
                suffix = Path(post.media_url.split("?")[0]).suffix or ".mp4"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                    temp.write(media_response.content)
                    temp_path = temp.name
                size = os.path.getsize(temp_path)
                init_response = await client.post(
                    "https://www.googleapis.com/upload/youtube/v3/videos",
                    params={"uploadType": "resumable", "part": "snippet,status"},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json; charset=UTF-8",
                        "X-Upload-Content-Length": str(size),
                        "X-Upload-Content-Type": content_type,
                    },
                    json={
                        "snippet": {
                            "title": (post.title or "Madani Islamic Academy Video")[:100],
                            "description": description[:5000],
                            "categoryId": str(category),
                            "tags": [tag.lstrip("#") for tag in post.hashtags[:500]],
                        },
                        "status": {"privacyStatus": privacy},
                    },
                )
                if init_response.status_code >= 400:
                    raise ProviderError(
                        f"YouTube upload initialization failed: {init_response.text}",
                        retryable=init_response.status_code >= 500,
                    )
                upload_url = init_response.headers.get("location")
                if not upload_url:
                    raise ProviderError("YouTube did not return a resumable upload URL")
                with open(temp_path, "rb") as media_file:
                    upload_response = await client.put(
                        upload_url,
                        headers={"Content-Type": content_type, "Content-Length": str(size)},
                        content=media_file.read(),
                    )
                try:
                    payload = upload_response.json()
                except ValueError:
                    payload = {"text": upload_response.text}
                if upload_response.status_code >= 400:
                    raise ProviderError(
                        f"YouTube upload failed with HTTP {upload_response.status_code}",
                        retryable=upload_response.status_code >= 500,
                        response=payload,
                    )
                video_id = str(payload.get("id") or "")
                if not video_id:
                    raise ProviderError("YouTube did not return a video ID", response=payload)
                return PublishResult(
                    external_id=video_id,
                    url=f"https://youtu.be/{video_id}",
                    raw=payload,
                )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
