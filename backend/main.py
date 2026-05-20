import json
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from backend.config import MODEL_REGISTRY, TAG_CONFIG
from backend.schemas import ChatRequest, RoutingRequest
from backend.models.router import suggest_model
from backend.services import chat_service, history_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    from backend.db.database import close_db
    close_db()
    for adapter in chat_service.adapters.values():
        await adapter.close()


app = FastAPI(title="Multi-Model Hub", version="1.0.0", lifespan=lifespan)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/models")
async def list_models():
    models = []
    for key, info in MODEL_REGISTRY.items():
        tag_names = [TAG_CONFIG[t]["name"] for t in info["tags"] if t in TAG_CONFIG]
        models.append({
            "key": key,
            "name": info["name"],
            "display_name": info["display_name"],
            "tags": tag_names,
            "description": info["description"],
            "enabled": info["enabled"],
        })
    return {"models": models, "tags": _get_tag_info()}


def _get_tag_info():
    return {k: {"name": v["name"], "keywords": v["keywords"]} for k, v in TAG_CONFIG.items()}


@app.post("/api/chat/send")
async def send_message(req: ChatRequest):
    async def event_stream():
        async for event in chat_service.chat_stream(
            message=req.message,
            conversation_id=req.conversation_id,
            model=req.model,
        ):
            data_str = json.dumps(event, ensure_ascii=False)
            yield f"data: {data_str}\n\n"
            await asyncio.sleep(0)
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/conversations")
async def list_conversations():
    conversations = history_service.get_conversations()
    return {"conversations": conversations}


@app.post("/api/conversations")
async def create_conversation():
    conv = history_service.create_conversation()
    return conv


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = history_service.get_conversation(conversation_id)
    if conv is None:
        return JSONResponse({"error": "对话不存在"}, status_code=404)
    return conv


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    history_service.delete_conversation(conversation_id)
    return {"ok": True}


@app.put("/api/conversations/{conversation_id}")
async def update_conversation_model(conversation_id: str, model: str = "auto"):
    history_service.update_model(conversation_id, model)
    return {"ok": True}


@app.post("/api/route/suggest")
async def suggest_route(req: RoutingRequest):
    return suggest_model(req.message)


@app.get("/health")
async def health():
    return {"status": "ok"}


frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    @app.get("/")
    async def index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
