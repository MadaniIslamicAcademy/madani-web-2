from fastapi import APIRouter, HTTPException, status

from app.dependencies import CsrfProtected, CurrentUser, DbSession
from app.models import Campaign
from app.schemas import CampaignCreate, CampaignRead, CampaignUpdate
from app.services.audit import record_audit
from app.services.campaigns import create_campaign, generate_campaign, get_campaign, list_campaigns

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=list[CampaignRead])
def all_campaigns(db: DbSession, user: CurrentUser) -> list[Campaign]:
    return list_campaigns(db)


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def new_campaign(data: CampaignCreate, db: DbSession, user: CurrentUser, csrf: CsrfProtected) -> Campaign:
    return create_campaign(db, data, user)


@router.get("/{campaign_id}", response_model=CampaignRead)
def one_campaign(campaign_id: str, db: DbSession, user: CurrentUser) -> Campaign:
    try:
        return get_campaign(db, campaign_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{campaign_id}", response_model=CampaignRead)
def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    db: DbSession,
    user: CurrentUser,
    csrf: CsrfProtected,
) -> Campaign:
    try:
        campaign = get_campaign(db, campaign_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)
    record_audit(db, action="campaign.updated", target_type="campaign", target_id=campaign.id, actor_user_id=user.id)
    db.commit()
    return get_campaign(db, campaign.id)


@router.post("/{campaign_id}/generate", response_model=CampaignRead)
def generate(
    campaign_id: str,
    db: DbSession,
    user: CurrentUser,
    csrf: CsrfProtected,
) -> Campaign:
    try:
        campaign = get_campaign(db, campaign_id)
        return generate_campaign(db, campaign, user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Content generation failed: {exc}") from exc
