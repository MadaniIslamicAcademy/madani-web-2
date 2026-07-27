from __future__ import annotations

import json
from typing import Any

import httpx

from app.providers.base import ProviderError


async def json_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    timeout: float = 45,
) -> tuple[httpx.Response, dict[str, Any]]:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
            data=data,
        )
    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = {"text": response.text}
    if response.status_code >= 400:
        retryable = response.status_code == 429 or response.status_code >= 500
        raise ProviderError(
            f"Provider returned HTTP {response.status_code}",
            retryable=retryable,
            response=payload,
        )
    return response, payload
