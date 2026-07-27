from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select

from app.dependencies import CsrfProtected, CurrentUser, DbSession
from app.models import User
from app.schemas import AuthResponse, LoginRequest, UserRead
from app.security import clear_auth_cookies, create_access_token, set_auth_cookies, verify_password
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, response: Response, request: Request, db: DbSession) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user.last_login_at = datetime.now(timezone.utc)
    token = create_access_token(user.id, user.role.value)
    csrf_token = set_auth_cookies(response, token)
    record_audit(
        db,
        action="auth.login",
        target_type="user",
        target_id=user.id,
        actor_user_id=user.id,
        metadata={"ip": request.client.host if request.client else ""},
    )
    db.commit()
    return AuthResponse(user=UserRead.model_validate(user), csrf_token=csrf_token)


@router.post("/logout", status_code=204)
def logout(response: Response, user: CurrentUser, db: DbSession, csrf: CsrfProtected) -> Response:
    clear_auth_cookies(response)
    record_audit(db, action="auth.logout", target_type="user", target_id=user.id, actor_user_id=user.id)
    db.commit()
    return response


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> User:
    return user
