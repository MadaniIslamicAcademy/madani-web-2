from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.router import api_router
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.enums import SocialProvider, UserRole
from app.models import SocialConnection, User
from app.security import hash_password


def bootstrap() -> None:
    if settings.environment in {"development", "test"}:
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).limit(1))
        if user is None:
            user = User(
                email=settings.bootstrap_admin_email.lower(),
                full_name="Madani Administrator",
                password_hash=hash_password(settings.bootstrap_admin_password),
                role=UserRole.SUPER_ADMIN,
            )
            db.add(user)
            db.flush()
        mock = db.scalar(select(SocialConnection).where(SocialConnection.provider == SocialProvider.MOCK))
        if mock is None:
            db.add(
                SocialConnection(
                    provider=SocialProvider.MOCK,
                    display_name="Safe Mock Publisher",
                    external_account_id="mock",
                    metadata_json={"purpose": "Development and approval testing"},
                    connected_by_id=user.id,
                )
            )
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.mount("/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "madani-social-api"}
