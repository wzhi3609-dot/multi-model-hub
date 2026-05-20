from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    model: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: str
    role: str
    content: str
    model: Optional[str] = None
    created_at: str


class ModelInfo(BaseModel):
    key: str
    name: str
    display_name: str
    tags: list[str]
    description: str
    enabled: bool


class RoutingRequest(BaseModel):
    message: str


class RoutingResponse(BaseModel):
    model: str
    model_name: str
    reason: str
    matched_tags: list[str]
