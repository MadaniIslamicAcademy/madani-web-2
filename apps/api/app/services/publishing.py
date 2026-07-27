from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import AttemptStatus, PostStatus, SocialProvider
from app.models import PublishAttempt, SocialConnection, SocialPost
from app.providers.base import ProviderError
from app.providers.factory import get_adapter
from app.services.audit import record_audit
from app.services.tokens import refresh_connection_if_needed


def find_connection(db: Session, post: SocialPost) -> SocialConnection | None:
    if post.connection_id:
        return db.get(SocialConnection, post.connection_id)
    provider = SocialProvider.MOCK if settings.social_publish_mode == "mock" else post.platform
    return db.scalar(
        select(SocialConnection)
        .where(SocialConnection.provider == provider, SocialConnection.is_active.is_(True))
        .order_by(SocialConnection.created_at.desc())
    )


async def publish_one(db: Session, post: SocialPost) -> SocialPost:
    if post.status not in {PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.FAILED}:
        raise ValueError(f"Post status {post.status} cannot be published")
    connection = find_connection(db, post)
    if connection is None:
        post.status = PostStatus.FAILED
        post.last_error = f"No active connection is available for {post.platform.value}"
        db.commit()
        return post
    connection = await refresh_connection_if_needed(db, connection)
    post.status = PostStatus.PUBLISHING
    attempt = PublishAttempt(
        post_id=post.id,
        attempt_number=post.retry_count + 1,
        status=AttemptStatus.STARTED,
    )
    db.add(attempt)
    db.commit()
    try:
        adapter = get_adapter(connection.provider)
        result = await adapter.publish(post, connection)
        post.status = PostStatus.PUBLISHED
        post.published_at = datetime.now(timezone.utc)
        post.external_post_id = result.external_id
        post.external_post_url = result.url
        post.last_error = ""
        attempt.status = AttemptStatus.SUCCEEDED
        attempt.provider_response = result.raw
        record_audit(db, action="post.published", target_type="post", target_id=post.id, metadata={"provider": connection.provider.value})
    except ProviderError as exc:
        post.retry_count += 1
        post.last_error = str(exc)
        attempt.status = AttemptStatus.FAILED
        attempt.error_message = str(exc)
        attempt.provider_response = exc.response
        if exc.retryable and post.retry_count < settings.max_publish_retries:
            post.status = PostStatus.SCHEDULED
            post.scheduled_for = datetime.now(timezone.utc)
        else:
            post.status = PostStatus.FAILED
        record_audit(db, action="post.failed", target_type="post", target_id=post.id, metadata={"error": str(exc)})
    except Exception as exc:
        post.retry_count += 1
        post.last_error = str(exc)
        post.status = PostStatus.FAILED
        attempt.status = AttemptStatus.FAILED
        attempt.error_message = str(exc)
        record_audit(db, action="post.failed", target_type="post", target_id=post.id, metadata={"error": str(exc)})
    db.commit()
    db.refresh(post)
    return post
