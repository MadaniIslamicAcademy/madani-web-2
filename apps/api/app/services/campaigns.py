from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.enums import CampaignStatus, PostStatus, SocialProvider
from app.models import Campaign, SocialPost, User
from app.schemas import CampaignCreate
from app.services.ai import get_content_generator
from app.services.audit import record_audit


def create_campaign(db: Session, data: CampaignCreate, user: User) -> Campaign:
    settings = dict(data.settings)
    settings["platforms"] = [p.value for p in data.platforms]
    campaign = Campaign(
        name=data.name,
        brief=data.brief,
        content_type=data.content_type,
        language=data.language,
        tone=data.tone,
        audience=data.audience,
        objective=data.objective,
        settings=settings,
        status=CampaignStatus.DRAFT,
        created_by_id=user.id,
    )
    db.add(campaign)
    db.flush()
    for platform in data.platforms:
        db.add(SocialPost(campaign_id=campaign.id, platform=platform, status=PostStatus.DRAFT))
    record_audit(db, action="campaign.created", target_type="campaign", target_id=campaign.id, actor_user_id=user.id)
    db.commit()
    return get_campaign(db, campaign.id)


def get_campaign(db: Session, campaign_id: str) -> Campaign:
    campaign = db.scalar(
        select(Campaign).where(Campaign.id == campaign_id).options(selectinload(Campaign.posts))
    )
    if campaign is None:
        raise LookupError("Campaign not found")
    return campaign


def generate_campaign(db: Session, campaign: Campaign, user: User) -> Campaign:
    platforms = [post.platform for post in campaign.posts]
    generated = get_content_generator().generate(campaign, platforms)
    for post in campaign.posts:
        item = generated.get(post.platform.value, {})
        post.title = str(item.get("title", ""))
        post.body = str(item.get("body", ""))
        post.hashtags = [str(tag).lstrip("#") for tag in item.get("hashtags", [])]
        post.call_to_action = str(item.get("call_to_action", ""))
        post.visual_idea = str(item.get("visual_idea", ""))
        post.status = PostStatus.GENERATED
        post.last_error = ""
    campaign.status = CampaignStatus.ACTIVE
    record_audit(db, action="campaign.generated", target_type="campaign", target_id=campaign.id, actor_user_id=user.id)
    db.commit()
    return get_campaign(db, campaign.id)


def list_campaigns(db: Session) -> list[Campaign]:
    return list(
        db.scalars(select(Campaign).options(selectinload(Campaign.posts)).order_by(Campaign.created_at.desc()))
    )
