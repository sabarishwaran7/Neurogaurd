"""Conversation memory backed by MongoDB chat_history collection."""

from datetime import datetime, timezone
from typing import Any, List

from pymongo.collection import Collection


def append_message(
    coll: Collection,
    *,
    user_id: str,
    agent_id: str,
    role: str,
    content: str,
) -> None:
    doc = {
        "user_id": user_id,
        "agent_id": agent_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc),
    }
    coll.insert_one(doc)


def recent_messages(coll: Collection, *, user_id: str, agent_id: str, limit: int = 20) -> List[dict[str, Any]]:
    cursor = (
        coll.find({"user_id": user_id, "agent_id": agent_id})
        .sort("created_at", 1)
        .limit(limit)
    )
    return [{"role": d["role"], "content": d["content"]} for d in cursor]


def recent_chats_for_user(coll: Collection, *, user_id: str, limit: int = 8) -> List[dict[str, Any]]:
    """Latest chat snippets across all agents for dashboard."""
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"created_at": -1}},
        {"$limit": 50},
        {"$group": {"_id": "$agent_id", "last": {"$first": "$$ROOT"}}},
        {"$limit": limit},
        {"$replaceRoot": {"newRoot": "$last"}},
    ]
    out: List[dict[str, Any]] = []
    for d in coll.aggregate(pipeline):
        out.append(
            {
                "agent_id": str(d.get("agent_id")),
                "role": d.get("role"),
                "content": (d.get("content") or "")[:200],
                "created_at": d.get("created_at").isoformat() if d.get("created_at") else None,
            }
        )
    return out
