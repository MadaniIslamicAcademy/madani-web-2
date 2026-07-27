from app.config import settings
from app.models import SocialConnection, SocialPost
from app.providers.base import ProviderError, PublishResult
from app.providers.helpers import json_request
from app.security import decrypt_secret


class WhatsAppAdapter:
    async def send_text(self, connection: SocialConnection, recipient: str, text: str) -> PublishResult:
        token = decrypt_secret(connection.access_token_encrypted)
        phone_number_id = connection.metadata_json.get("phone_number_id") or connection.external_account_id
        if not token or not phone_number_id:
            raise ProviderError("WhatsApp token and Phone Number ID are required")
        body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        _, payload = await json_request(
            "POST",
            f"https://graph.facebook.com/{settings.meta_graph_version}/{phone_number_id}/messages",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json_body=body,
        )
        message_id = str((payload.get("messages") or [{}])[0].get("id") or "")
        if not message_id:
            raise ProviderError("WhatsApp did not return a message ID", response=payload)
        return PublishResult(external_id=message_id, raw=payload)

    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult:
        recipient = post.provider_payload.get("recipient")
        recipients = post.provider_payload.get("recipients") or ([] if not recipient else [recipient])
        if not recipients:
            raise ProviderError("WhatsApp post requires recipient or recipients in provider payload")
        token = decrypt_secret(connection.access_token_encrypted)
        phone_number_id = connection.metadata_json.get("phone_number_id") or connection.external_account_id
        if not token or not phone_number_id:
            raise ProviderError("WhatsApp token and Phone Number ID are required")
        template_name = post.provider_payload.get("template_name")
        language_code = post.provider_payload.get("template_language", "en")
        message_ids: list[str] = []
        raw: list[dict] = []
        for recipient_value in recipients:
            if template_name:
                body = {
                    "messaging_product": "whatsapp",
                    "to": recipient_value,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": language_code},
                        "components": post.provider_payload.get("template_components", []),
                    },
                }
                _, payload = await json_request(
                    "POST",
                    f"https://graph.facebook.com/{settings.meta_graph_version}/{phone_number_id}/messages",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json_body=body,
                )
                message_id = str((payload.get("messages") or [{}])[0].get("id") or "")
                if not message_id:
                    raise ProviderError("WhatsApp did not return a message ID", response=payload)
                result = PublishResult(message_id, raw=payload)
            else:
                result = await self.send_text(connection, str(recipient_value), post.body)
            message_ids.append(result.external_id)
            raw.append(result.raw)
        return PublishResult(external_id=",".join(message_ids), raw={"messages": raw})
