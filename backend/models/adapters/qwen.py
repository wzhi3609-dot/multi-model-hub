import json
import logging
import httpx
from backend.config import QWEN_API_KEY, QWEN_BASE_URL
from backend.models.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class QwenAdapter(BaseAdapter):
    def __init__(self, api_model: str = "qwen-plus"):
        self.api_model = api_model
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=QWEN_BASE_URL,
                headers={
                    "Authorization": f"Bearer {QWEN_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def chat_stream(self, messages: list[dict], **kwargs):
        client = self._get_client()
        request_body = {
            "model": self.api_model,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        async with client.stream(
            "POST", "/chat/completions", json=request_body
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        logger.warning("Failed to parse SSE chunk: %s | raw: %.200s", e, data_str)
                        continue

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
