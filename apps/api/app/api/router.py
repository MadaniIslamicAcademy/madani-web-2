from fastapi import APIRouter

from app.api import audit, auth, campaigns, connections, dashboard, leads, media, oauth, posts, webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(audit.router)
api_router.include_router(media.router)
api_router.include_router(dashboard.router)
api_router.include_router(campaigns.router)
api_router.include_router(posts.router)
api_router.include_router(connections.router)
api_router.include_router(leads.router)
api_router.include_router(oauth.router)
api_router.include_router(webhooks.router)
