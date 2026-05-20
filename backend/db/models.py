import uuid
from datetime import datetime, timezone
from backend.db.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def create_conversation(title: str | None = None, model: str = "auto") -> dict:
    conv_id = str(uuid.uuid4())
    now = _now()
    db = get_db()
    db.execute(
        "INSERT INTO conversations (id, title, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (conv_id, title, model, now, now),
    )
    db.commit()
    return {"id": conv_id, "title": title, "model": model, "created_at": now, "updated_at": now}


def get_conversation(conv_id: str) -> dict | None:
    db = get_db()
    row = db.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    if row is None:
        return None
    return dict(row)


def list_conversations() -> list[dict]:
    db = get_db()
    rows = db.execute("SELECT * FROM conversations ORDER BY updated_at DESC").fetchall()
    return [dict(r) for r in rows]


def update_conversation_title(conv_id: str, title: str):
    db = get_db()
    db.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
        (title, _now(), conv_id),
    )
    db.commit()


def update_conversation_model(conv_id: str, model: str):
    db = get_db()
    db.execute(
        "UPDATE conversations SET model = ?, updated_at = ? WHERE id = ?",
        (model, _now(), conv_id),
    )
    db.commit()


def touch_conversation(conv_id: str):
    db = get_db()
    db.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (_now(), conv_id))
    db.commit()


def delete_conversation(conv_id: str):
    db = get_db()
    db.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    db.commit()


def add_message(conv_id: str, role: str, content: str, model: str | None = None) -> dict:
    db = get_db()
    now = _now()
    cursor = db.execute(
        "INSERT INTO messages (conversation_id, role, content, model, created_at) VALUES (?, ?, ?, ?, ?)",
        (conv_id, role, content, model, now),
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "conversation_id": conv_id,
        "role": role,
        "content": content,
        "model": model,
        "created_at": now,
    }


def get_messages(conv_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conv_id,),
    ).fetchall()
    return [dict(r) for r in rows]
