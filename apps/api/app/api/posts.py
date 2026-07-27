from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.dependencies import CsrfProtected, CurrentUser, DbSession
from app.enums import PostStatus
from app.models import SocialConnection, SocialPost
from app.schemas import PostRead, PostUpdate, ScheduleRequest
from app.services.audit import record_audit

router = APIRouter(prefix="/posts", tags=["Posts"])


def find_post(db: DbSession, post_id: str) -> SocialPost:
    post = db.get(SocialPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.patch("/{post_id}", response_model=PostRead)
def update_post(
    post_id: str,
    data: PostUpdate,
    db: DbSession,
    user: CurrentUser,
    csrf: CsrfProtected,
) -> SocialPost:
    post = find_post(db, post_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(post, key, value)
    if post.status in {PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.FAILED}:
        post.status = PostStatus.GENERATED
        post.approved_at = None
        post.approved_by_id = None
    record_audit(db, action="post.updated", target_type="post", target_id=post.id, actor_user_id=user.id)
    db.commit()
    db.refresh(post)
    return post


@router.post("/{post_id}/approve", response_model=PostRead)
def approve_post(post_id: str, db: DbSession, user: CurrentUser, csrf: CsrfProtected) -> SocialPost:
    post = find_post(db, post_id)
    if not post.body.strip():
        raise HTTPException(status_code=400, detail="Post content is empty")
    post.status = PostStatus.APPROVED
    post.approved_at = datetime.now(timezone.utc)
    post.approved_by_id = user.id
    record_audit(db, action="post.approved", target_type="post", target_id=post.id, actor_user_id=user.id)
    db.commit()
    db.refresh(post)
    return post


@router.post("/{post_id}/schedule", response_model=PostRead)
def schedule_post(
    post_id: str,
    data: ScheduleRequest,
    db: DbSession,
    user: CurrentUser,
    csrf: CsrfProtected,
) -> SocialPost:
    post = find_post(db, post_id)
    if post.status not in {PostStatus.APPROVED, PostStatus.SCHEDULED}:
        raise HTTPException(status_code=400, detail="Approve the post before scheduling")
    if data.scheduled_for <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")
    post.scheduled_for = data.scheduled_for
    post.status = PostStatus.SCHEDULED
    record_audit(db, action="post.scheduled", target_type="post", target_id=post.id, actor_user_id=user.id, metadata={"scheduled_for": data.scheduled_for.isoformat()})
    db.commit()
    db.refresh(post)
    return post


@router.post("/{post_id}/publish", response_model=PostRead)
def publish_now(post_id: str, db: DbSession, user: CurrentUser, csrf: CsrfProtected) -> SocialPost:
    post = find_post(db, post_id)
    if post.status not in {PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.FAILED}:
        raise HTTPException(status_code=400, detail="Approve the post before publishing")
    if post.connection_id and not db.get(SocialConnection, post.connection_id):
        raise HTTPException(status_code=400, detail="Selected connection does not exist")
    from app.worker import publish_post

    publish_post.delay(post.id)
    record_audit(db, action="post.queued", target_type="post", target_id=post.id, actor_user_id=user.id)
    db.commit()
    return post


@router.post("/{post_id}/cancel", response_model=PostRead)
def cancel_post(post_id: str, db: DbSession, user: CurrentUser, csrf: CsrfProtected) -> SocialPost:
    post = find_post(db, post_id)
    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Published posts cannot be cancelled")
    post.status = PostStatus.CANCELLED
    record_audit(db, action="post.cancelled", target_type="post", target_id=post.id, actor_user_id=user.id)
    db.commit()
    db.refresh(post)
    return post
