from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.models import SocialConnection, SocialPost


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False, response: dict[str, Any] | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.response = response or {}


@dataclass(slots=True)
class PublishResult:
    external_id: str
    url: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class ProviderAdapter(Protocol):
    async def publish(self, post: SocialPost, connection: SocialConnection) -> PublishResult: ...
