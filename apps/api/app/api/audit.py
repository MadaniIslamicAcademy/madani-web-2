from fastapi import APIRouter, Query
from sqlalchemy import select

from app.dependencies import AdminUser, DbSession
from app.models import AuditLog
from app.schemas import AuditRead

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditRead])
def list_audit_events(
    db: DbSession,
    user: AdminUser,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)))
