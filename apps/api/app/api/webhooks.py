from typing import Any
import hashlib
import hmac
import json

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.db import SessionLocal
from app.services.admissions import process_inbound_message

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/whatsapp")
def verify_whatsapp(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
) -> PlainTextResponse:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


async def handle_whatsapp_payload(payload: dict[str, Any]) -> None:
    entries = payload.get("entry") or []
    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            phone_number_id = str((value.get("metadata") or {}).get("phone_number_id") or "")
            contacts = value.get("contacts") or []
            contact_by_id = {str(item.get("wa_id")): item for item in contacts}
            for message in value.get("messages") or []:
                if message.get("type") != "text":
                    continue
                sender = str(message.get("from") or "")
                text = str((message.get("text") or {}).get("body") or "")
                if not sender or not text:
                    continue
                contact = contact_by_id.get(sender, {})
                with SessionLocal() as db:
                    await process_inbound_message(
                        db,
                        whatsapp_user_id=sender,
                        phone_number=sender,
                        message_id=str(message.get("id") or ""),
                        text=text,
                        raw_payload={"message": message, "contact": contact},
                        phone_number_id=phone_number_id,
                    )


@router.post("/whatsapp", status_code=200)
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, bool]:
    raw = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if settings.meta_app_secret and signature:
        expected = "sha256=" + hmac.new(settings.meta_app_secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
    payload = json.loads(raw or b"{}")
    background_tasks.add_task(handle_whatsapp_payload, payload)
    return {"received": True}
