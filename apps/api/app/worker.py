import asyncio
from datetime import datetime, timezone

from celery import Celery
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.enums import PostStatus
from app.models import SocialPost
from app.services.publishing import publish_one

celery_app = Celery("madani_social", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = settings.timezone
celery_app.conf.beat_schedule = {
    "enqueue-due-posts-every-minute": {
        "task": "app.worker.enqueue_due_posts",
        "schedule": 60.0,
    }
}


@celery_app.task(name="app.worker.enqueue_due_posts")
def enqueue_due_posts() -> int:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        ids = list(
            db.scalars(
                select(SocialPost.id).where(
                    SocialPost.status.in_([PostStatus.SCHEDULED, PostStatus.APPROVED]),
                    SocialPost.scheduled_for.is_not(None),
                    SocialPost.scheduled_for <= now,
                )
            )
        )
    for post_id in ids:
        publish_post.delay(post_id)
    return len(ids)


@celery_app.task(name="app.worker.publish_post", bind=True, max_retries=3)
def publish_post(self, post_id: str) -> str:
    with SessionLocal() as db:
        post = db.get(SocialPost, post_id)
        if not post:
            return "missing"
        asyncio.run(publish_one(db, post))
        return post.status.value
