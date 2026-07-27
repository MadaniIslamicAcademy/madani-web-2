from __future__ import annotations

import json
import re
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import LeadStatus, SocialProvider
from app.models import AdmissionLead, AdmissionMessage, SocialConnection
from app.providers.whatsapp import WhatsAppAdapter

FIELDS = ["student_name", "father_name", "age", "course", "preferred_days", "preferred_time", "country"]
QUESTIONS = {
    "student_name": "Please share the student’s full name.",
    "father_name": "Please share the father or guardian’s name.",
    "age": "Please share the student’s age.",
    "course": "Which course would you like to join?",
    "preferred_days": "Which days would you prefer for classes?",
    "preferred_time": "What time would you prefer? Our Admissions Department will confirm availability.",
    "country": "Which country are you contacting us from?",
}


def get_or_create_lead(db: Session, whatsapp_user_id: str, phone_number: str) -> AdmissionLead:
    lead = db.scalar(select(AdmissionLead).where(AdmissionLead.whatsapp_user_id == whatsapp_user_id))
    if lead:
        return lead
    lead = AdmissionLead(
        whatsapp_user_id=whatsapp_user_id,
        phone_number=phone_number,
        status=LeadStatus.COLLECTING,
    )
    db.add(lead)
    db.flush()
    return lead


def _fallback_extract(lead: AdmissionLead, text: str) -> dict[str, str]:
    missing = [field for field in FIELDS if not getattr(lead, field)]
    if not missing:
        return {}
    current = missing[0]
    value = text.strip()
    if current == "age":
        match = re.search(r"\b\d{1,2}\b", value)
        value = match.group(0) if match else value
    return {current: value[:160]}


def extract_details(lead: AdmissionLead, text: str) -> dict[str, str]:
    if not settings.openai_api_key or OpenAI is None:
        return _fallback_extract(lead, text)
    client = OpenAI(api_key=settings.openai_api_key)
    known = {field: getattr(lead, field) for field in FIELDS}
    prompt = f"""Extract only explicitly stated admission details from the latest WhatsApp message.
Known details: {json.dumps(known, ensure_ascii=False)}
Latest message: {text}
Return a JSON object with any of these keys only: {', '.join(FIELDS)}.
Do not guess. Do not calculate or confirm fees, discounts, teacher availability or class timing.
"""
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
        store=False,
        text={"format": {"type": "json_object"}},
    )
    try:
        data = json.loads(response.output_text)
    except json.JSONDecodeError:
        return _fallback_extract(lead, text)
    return {key: str(value)[:160] for key, value in data.items() if key in FIELDS and value}


def update_lead(lead: AdmissionLead, values: dict[str, str]) -> None:
    for field, value in values.items():
        if field in FIELDS and value and not getattr(lead, field):
            setattr(lead, field, value)
    lead.details_json = {field: getattr(lead, field) for field in FIELDS}


def build_reply(lead: AdmissionLead) -> str:
    missing = [field for field in FIELDS if not getattr(lead, field)]
    if missing:
        lead.status = LeadStatus.COLLECTING
        return QUESTIONS[missing[0]]
    lead.status = LeadStatus.READY_FOR_TEAM
    lead.summary = (
        "New Admission Summary\n"
        f"Student Name: {lead.student_name}\n"
        f"Father or Guardian: {lead.father_name}\n"
        f"Age: {lead.age}\n"
        f"Course: {lead.course}\n"
        f"Preferred Days: {lead.preferred_days}\n"
        f"Preferred Time: {lead.preferred_time}\n"
        f"Country: {lead.country}\n"
        f"Phone: {lead.phone_number}"
    )
    return (
        "جزاك الله خيرا. Your admission details have been recorded. "
        "Our Admissions Department will contact you and confirm the available days, times and applicable fee. "
        "For the official fee structure, please visit https://madaniislamicacademy.com/fee-structure/"
    )


async def process_inbound_message(
    db: Session,
    *,
    whatsapp_user_id: str,
    phone_number: str,
    message_id: str,
    text: str,
    raw_payload: dict[str, Any],
    phone_number_id: str,
) -> str:
    lead = get_or_create_lead(db, whatsapp_user_id, phone_number)
    db.add(AdmissionMessage(lead_id=lead.id, direction="inbound", message_id=message_id, text=text, raw_payload=raw_payload))
    update_lead(lead, extract_details(lead, text))
    reply = build_reply(lead)
    db.add(AdmissionMessage(lead_id=lead.id, direction="outbound", text=reply))
    db.commit()

    connection = db.scalar(
        select(SocialConnection).where(
            SocialConnection.provider == SocialProvider.WHATSAPP,
            SocialConnection.is_active.is_(True),
        )
    )
    if connection and (connection.metadata_json.get("phone_number_id") == phone_number_id or connection.external_account_id == phone_number_id):
        await WhatsAppAdapter().send_text(connection, phone_number, reply)
    return reply
