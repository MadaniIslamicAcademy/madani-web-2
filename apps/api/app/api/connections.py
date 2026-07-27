from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import AdminUser, CsrfProtected, DbSession
from app.models import SocialConnection
from app.schemas import ConnectionCreate, ConnectionRead, ConnectionUpdate
from app.security import encrypt_secret
from app.services.audit import record_audit

router = APIRouter(prefix="/connections", tags=["Connections"])


@router.get("", response_model=list[ConnectionRead])
def list_connections(db: DbSession, user: AdminUser) -> list[SocialConnection]:
    return list(db.scalars(select(SocialConnection).order_by(SocialConnection.created_at.desc())))


@router.post("", response_model=ConnectionRead, status_code=status.HTTP_201_CREATED)
def create_connection(
    data: ConnectionCreate,
    db: DbSession,
    user: AdminUser,
    csrf: CsrfProtected,
) -> SocialConnection:
    connection = SocialConnection(
        provider=data.provider,
        display_name=data.display_name,
        external_account_id=data.external_account_id,
        access_token_encrypted=encrypt_secret(data.access_token),
        refresh_token_encrypted=encrypt_secret(data.refresh_token),
        token_expires_at=data.token_expires_at,
        metadata_json=data.metadata_json,
        connected_by_id=user.id,
    )
    db.add(connection)
    db.flush()
    record_audit(db, action="connection.created", target_type="connection", target_id=connection.id, actor_user_id=user.id, metadata={"provider": data.provider.value})
    db.commit()
    db.refresh(connection)
    return connection


@router.patch("/{connection_id}", response_model=ConnectionRead)
def update_connection(
    connection_id: str,
    data: ConnectionUpdate,
    db: DbSession,
    user: AdminUser,
    csrf: CsrfProtected,
) -> SocialConnection:
    connection = db.get(SocialConnection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    values = data.model_dump(exclude_unset=True)
    if "access_token" in values:
        connection.access_token_encrypted = encrypt_secret(values.pop("access_token") or "")
    if "refresh_token" in values:
        connection.refresh_token_encrypted = encrypt_secret(values.pop("refresh_token") or "")
    for key, value in values.items():
        setattr(connection, key, value)
    record_audit(db, action="connection.updated", target_type="connection", target_id=connection.id, actor_user_id=user.id)
    db.commit()
    db.refresh(connection)
    return connection


@router.post("/{connection_id}/toggle", response_model=ConnectionRead)
def toggle_connection(
    connection_id: str,
    db: DbSession,
    user: AdminUser,
    csrf: CsrfProtected,
) -> SocialConnection:
    connection = db.get(SocialConnection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    connection.is_active = not connection.is_active
    record_audit(db, action="connection.toggled", target_type="connection", target_id=connection.id, actor_user_id=user.id, metadata={"active": connection.is_active})
    db.commit()
    db.refresh(connection)
    return connection


@router.delete("/{connection_id}", status_code=204)
def delete_connection(
    connection_id: str,
    db: DbSession,
    user: AdminUser,
    csrf: CsrfProtected,
) -> None:
    connection = db.get(SocialConnection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    record_audit(db, action="connection.deleted", target_type="connection", target_id=connection.id, actor_user_id=user.id)
    db.delete(connection)
    db.commit()
