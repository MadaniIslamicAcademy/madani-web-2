from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DbSession
from app.enums import LeadStatus, PostStatus
from app.models import AdmissionLead, Campaign, SocialConnection, SocialPost
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: DbSession, user: CurrentUser) -> DashboardSummary:
    scalar = lambda stmt: int(db.scalar(stmt) or 0)
    return DashboardSummary(
        campaigns=scalar(select(func.count()).select_from(Campaign)),
        draft_posts=scalar(select(func.count()).select_from(SocialPost).where(SocialPost.status.in_([PostStatus.DRAFT, PostStatus.GENERATED]))),
        scheduled_posts=scalar(select(func.count()).select_from(SocialPost).where(SocialPost.status == PostStatus.SCHEDULED)),
        published_posts=scalar(select(func.count()).select_from(SocialPost).where(SocialPost.status == PostStatus.PUBLISHED)),
        failed_posts=scalar(select(func.count()).select_from(SocialPost).where(SocialPost.status == PostStatus.FAILED)),
        new_leads=scalar(select(func.count()).select_from(AdmissionLead).where(AdmissionLead.status.in_([LeadStatus.NEW, LeadStatus.READY_FOR_TEAM]))),
        active_connections=scalar(select(func.count()).select_from(SocialConnection).where(SocialConnection.is_active.is_(True))),
    )
