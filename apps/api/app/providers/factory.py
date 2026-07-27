from app.enums import SocialProvider
from app.providers.base import ProviderAdapter
from app.providers.facebook import FacebookAdapter
from app.providers.instagram import InstagramAdapter
from app.providers.linkedin import LinkedInAdapter
from app.providers.mock import MockAdapter
from app.providers.tiktok import TikTokAdapter
from app.providers.whatsapp import WhatsAppAdapter
from app.providers.x_provider import XAdapter
from app.providers.youtube import YouTubeAdapter


def get_adapter(provider: SocialProvider) -> ProviderAdapter:
    adapters: dict[SocialProvider, type] = {
        SocialProvider.MOCK: MockAdapter,
        SocialProvider.FACEBOOK: FacebookAdapter,
        SocialProvider.INSTAGRAM: InstagramAdapter,
        SocialProvider.LINKEDIN: LinkedInAdapter,
        SocialProvider.WHATSAPP: WhatsAppAdapter,
        SocialProvider.YOUTUBE: YouTubeAdapter,
        SocialProvider.TIKTOK: TikTokAdapter,
        SocialProvider.X: XAdapter,
    }
    try:
        return adapters[provider]()
    except KeyError as exc:
        raise ValueError(f"No adapter registered for {provider}") from exc
