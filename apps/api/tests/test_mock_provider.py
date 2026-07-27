import asyncio
from types import SimpleNamespace

from app.providers.mock import MockAdapter


def test_mock_publish_returns_id() -> None:
    post = SimpleNamespace(platform=SimpleNamespace(value="facebook"))
    connection = SimpleNamespace(display_name="Mock")
    result = asyncio.run(MockAdapter().publish(post, connection))
    assert result.external_id.startswith("mock_")
