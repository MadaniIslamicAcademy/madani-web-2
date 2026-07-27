from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import UserRole
from app.models import User
from app.security import ACCESS_COOKIE, decode_access_token, require_csrf

DbSession = Annotated[Session, Depends(get_db)]


def current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
CsrfProtected = Annotated[None, Depends(require_csrf)]


def require_admin(user: CurrentUser) -> User:
    if user.role not in {UserRole.SUPER_ADMIN, UserRole.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
