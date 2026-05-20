from typing import AsyncGenerator
from backend.db import models as db_models
from backend.models.router import suggest_model
from backend.models.adapters.groq import GroqAdapter
from backend.models.adapters.qwen import QwenAdapter
from backend.config import MODEL_REGISTRY

_adapters = {}


def _get_adapter(model_key: str, model_config: dict):
    if model_key not in _adapters:
        provider = model_config["provider"]
        api_model = model_config["api_model"]
        if provider == "groq":
            _adapters[model_key] = GroqAdapter(api_model=api_model)
        elif provider == "qwen":
            _adapters[model_key] = QwenAdapter(api_model=api_model)
    return _adapters[model_key]


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

    db_models.update_conversation_model(conversation_id, model)

    db_models.add_message(conversation_id, "user", message)

    history = db_models.get_messages(conversation_id)
    api_messages = _format_messages(history)

    adapter = _get_adapter(model, model_config)
    full_response = ""

    try:
        async for token in adapter.chat_stream(api_messages):
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
        yield {"type": "error", "message": str(e)}


def _format_messages(history: list[dict]) -> list[dict]:
    result = []
    for msg in history:
        role = msg["role"]
        if role == "assistant":
            role = "assistant"
        elif role == "user":
            role = "user"
        result.append({"role": role, "content": msg["content"]})
    return result
