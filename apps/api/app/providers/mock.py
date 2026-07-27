from uuid import uuid4

from app.models import SocialConnection, SocialPost
from app.providers.base import PublishResult


class MockAdapter:
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        external_id = f"mock_{uuid4().hex}"
        return PublishResult(
            external_id=external_id,
            url=f"https://example.invalid/mock/{external_id}",
            raw={"mock": True, "platform": post.platform.value, "connection": connection.display_name},
        )
