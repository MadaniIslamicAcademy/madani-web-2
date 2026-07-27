from __future__ import annotations

import json
from typing import Any, Protocol

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app.config import settings
from app.enums import SocialProvider
from app.models import Campaign


class ContentGenerator(Protocol):
    def generate(self, campaign: Campaign, platforms: list[SocialProvider]) -> dict[str, dict[str, Any]]: ...


ACADEMY_RULES = """
You write social media content for Madani Islamic Academy Ltd.
Use the exact phrases “Two Day Free Trial” and “Teaching Since 2010” when relevant.
Never invent or confirm a class time, teacher availability, discount or final fee.
For fee questions, direct readers to https://madaniislamicacademy.com/fee-structure/ and say the Admissions Department will confirm the applicable amount.
For trial time requests, say the Admissions Department will contact the family and confirm available days and times.
Keep Islamic wording respectful and do not make exaggerated promises.
Keep Arabic phrases such as السلام عليكم، الحمد لله، ما شاء الله، and جزاك الله خيرا in Arabic script.
""".strip()


class OpenAIContentGenerator:
    def __init__(self) -> None:
        if OpenAI is None:
            raise RuntimeError("The openai package is not installed")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, campaign: Campaign, platforms: list[SocialProvider]) -> dict[str, dict[str, Any]]:
        platform_names = [platform.value for platform in platforms]
        schema = {
            "type": "object",
            "properties": {
                name: {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "hashtags": {"type": "array", "items": {"type": "string"}},
                        "call_to_action": {"type": "string"},
                        "visual_idea": {"type": "string"},
                    },
                    "required": ["title", "body", "hashtags", "call_to_action", "visual_idea"],
                    "additionalProperties": False,
                }
                for name in platform_names
            },
            "required": platform_names,
            "additionalProperties": False,
        }
        prompt = f"""{ACADEMY_RULES}

Create separate native content for these platforms: {', '.join(platform_names)}.
Campaign name: {campaign.name}
Brief and facts: {campaign.brief}
Content type: {campaign.content_type}
Language: {campaign.language}
Tone: {campaign.tone}
Audience: {campaign.audience}
Objective: {campaign.objective}
Settings: {json.dumps(campaign.settings, ensure_ascii=False)}

Platform requirements:
Facebook should be warm and community focused.
Instagram needs a strong opening line, clean spacing and a visual idea.
LinkedIn should be professional and education focused.
WhatsApp should be concise, easy to forward and normally avoid hashtags.
YouTube needs a searchable title and useful description.
X should normally remain within 280 characters.
TikTok needs a concise caption and must not promise unsupported results.
"""
        response = self.client.responses.create(
            model=settings.openai_model,
            input=prompt,
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "social_content",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        return json.loads(response.output_text)


class TemplateContentGenerator:
    def generate(self, campaign: Campaign, platforms: list[SocialProvider]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        website = campaign.settings.get("website_url", "https://madaniislamicacademy.com/")
        whatsapp = campaign.settings.get("whatsapp_number", "+44 7480 676283")
        fee_intent = any(word in campaign.brief.lower() for word in ["fee", "price", "discount", "فیس", "قیمت"])
        for platform in platforms:
            body = (
                f"📖 {campaign.brief}\n\n"
                "Give your family a clear and structured path to Quran learning. "
                "Start with a Two Day Free Trial. Our Admissions Department will contact you "
                "to confirm the available days and times.\n\nTeaching Since 2010"
            )
            if fee_intent:
                body += "\n\nFee details: https://madaniislamicacademy.com/fee-structure/"
            if platform == SocialProvider.WHATSAPP:
                body += f"\n\nWhatsApp: {whatsapp}"
                hashtags: list[str] = []
            else:
                body += f"\n\nLearn more: {website}"
                hashtags = ["MadaniIslamicAcademy", "OnlineQuranClasses", "QuranLearning"]
            if platform == SocialProvider.X:
                body = body[:278]
            result[platform.value] = {
                "title": f"{campaign.name} | Madani Islamic Academy",
                "body": body,
                "hashtags": hashtags,
                "call_to_action": f"Learn more: {website}",
                "visual_idea": "Use the academy dark green and yellow branding with a short readable headline.",
            }
        return result


def get_content_generator() -> ContentGenerator:
    if settings.ai_provider == "openai" and settings.openai_api_key and OpenAI is not None:
        return OpenAIContentGenerator()
    return TemplateContentGenerator()
