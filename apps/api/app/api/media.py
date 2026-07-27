from fastapi import APIRouter, File, HTTPException, UploadFile

from app.dependencies import CsrfProtected, CurrentUser
from app.services.storage import save_upload

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/upload")
async def upload_media(user: CurrentUser, csrf: CsrfProtected, file: UploadFile = File(...)) -> dict:
    try:
        return await save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
