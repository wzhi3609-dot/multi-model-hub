import asyncio
import logging
from typing import AsyncGenerator
from backend.db import models as db_models
from backend.models.router import suggest_model
from backend.models.adapters.groq import GroqAdapter
from backend.models.adapters.qwen import QwenAdapter
from backend.config import MODEL_REGISTRY

logger = logging.getLogger(__name__)

adapters = {}
_lock = asyncio.Lock()
MAX_HISTORY_MESSAGES = 30
MAX_RETRIES = 2
RETRY_BASE_DELAY = 1.0


async def _get_adapter(model_key: str, model_config: dict):
    if model_key not in adapters:
        async with _lock:
            if model_key not in adapters:
                provider = model_config["provider"]
                api_model = model_config["api_model"]
                if provider == "groq":
                    adapters[model_key] = GroqAdapter(api_model=api_model)
                elif provider == "qwen":
                    adapters[model_key] = QwenAdapter(api_model=api_model)
    return adapters[model_key]


async def chat_stream(
    message: str,
    conversation_id: str | None = None,
    model: str | None = None,
) -> AsyncGenerator[dict, None]:
    if conversation_id is None:
        conv = db_models.create_conversation(model=model or "auto")
        conversation_id = conv["id"]
        yield {"type": "conversation_id", "id": conversation_id}
    else:
        conv = db_models.get_conversation(conversation_id)
        if conv is None:
            conv = db_models.create_conversation(model=model or "auto")
            conversation_id = conv["id"]
            yield {"type": "conversation_id", "id": conversation_id}

    if model is None or model == "auto":
        routing = suggest_model(message)
        if not routing["model"]:
            yield {"type": "error", "message": routing["reason"]}
            return
        model = routing["model"]
        yield {"type": "routing", "model": model, "model_name": routing["model_name"],
               "reason": routing["reason"], "matched_tags": routing["matched_tags"]}

    model_config = MODEL_REGISTRY.get(model)
    if not model_config or not model_config["enabled"]:
        enabled_models = {k: v for k, v in MODEL_REGISTRY.items() if v["enabled"]}
        if not enabled_models:
            yield {"type": "error", "message": "没有可用的模型，请先配置 API Key"}
            return
        model = next(iter(enabled_models))
        model_config = enabled_models[model]
        yield {"type": "routing", "model": model, "model_name": model_config["name"],
               "reason": "指定模型不可用，回退到可用模型", "matched_tags": []}

    db_models.add_message(conversation_id, "user", message)
    db_models.update_conversation_model(conversation_id, model)

    history = db_models.get_messages(conversation_id)
    api_messages = _format_messages(history)

    adapter = await _get_adapter(model, model_config)
    full_response = ""

    try:
        async for token in _stream_with_retry(adapter, api_messages):
            full_response += token
            yield {"type": "token", "content": token}

        db_models.add_message(conversation_id, "assistant", full_response, model=model_config["display_name"])

        conv = db_models.get_conversation(conversation_id)
        if conv and not conv.get("title"):
            title = message[:30] + ("..." if len(message) > 30 else "")
            db_models.update_conversation_title(conversation_id, title)

        db_models.touch_conversation(conversation_id)
        yield {"type": "done"}

    except Exception as e:
        logger.error("Chat stream error for model %s: %s", model, e)
        yield {"type": "error", "message": str(e)}


async def _stream_with_retry(adapter, messages, retries=MAX_RETRIES):
    last_error = None
    for attempt in range(retries + 1):
        try:
            async for token in adapter.chat_stream(messages):
                yield token
            return
        except Exception as e:
            last_error = e
            if attempt < retries:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning("Retry %d/%d after %.1fs: %s", attempt + 1, retries, delay, e)
                await asyncio.sleep(delay)
    raise last_error


def _format_messages(history: list[dict]) -> list[dict]:
    result = []
    if len(history) > MAX_HISTORY_MESSAGES:
        history = history[-MAX_HISTORY_MESSAGES:]
    for msg in history:
        role = msg["role"]
        if role not in ("user", "assistant", "system"):
            role = "user"
        result.append({"role": role, "content": msg["content"]})
    return result
