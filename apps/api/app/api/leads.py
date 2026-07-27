from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import CsrfProtected, CurrentUser, DbSession
from app.models import AdmissionLead
from app.schemas import LeadRead, LeadUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/leads", tags=["Admission leads"])


@router.get("", response_model=list[LeadRead])
def list_leads(db: DbSession, user: CurrentUser) -> list[AdmissionLead]:
    return list(db.scalars(select(AdmissionLead).order_by(AdmissionLead.created_at.desc())))


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: str,
    data: LeadUpdate,
    db: DbSession,
    user: CurrentUser,
    csrf: CsrfProtected,
) -> AdmissionLead:
    lead = db.get(AdmissionLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
    record_audit(db, action="lead.updated", target_type="lead", target_id=lead.id, actor_user_id=user.id)
    db.commit()
    db.refresh(lead)
    return lead
