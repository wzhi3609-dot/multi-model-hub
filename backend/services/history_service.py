from backend.db import models as db_models


def get_conversations() -> list[dict]:
    return db_models.list_conversations()


def create_conversation(model: str = "auto") -> dict:
    return db_models.create_conversation(model=model)


def get_conversation(conversation_id: str) -> dict | None:
    conv = db_models.get_conversation(conversation_id)
    if conv is None:
        return None
    messages = db_models.get_messages(conversation_id)
    conv["messages"] = messages
    return conv


def delete_conversation(conversation_id: str):
    db_models.delete_conversation(conversation_id)


def update_model(conversation_id: str, model: str):
    db_models.update_conversation_model(conversation_id, model)
