"""Agent CRUD, dashboard, chat, public API execution."""

import shutil
from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from limiter_config import limiter
from starlette.concurrency import run_in_threadpool

from config import UPLOADS_ROOT, VECTOR_ROOT
from database import get_db
from models.schemas import (
    AgentCreate,
    AgentOut,
    AgentUpdate,
    ChatRequest,
    ChatResponse,
    DashboardStats,
    ExternalAgentChatRequest,
    ExternalAgentChatResponse,
)
from services.langgraph_service import build_agent_app
from services.memory_service import append_message, recent_chats_for_user, recent_messages
from services.usage_service import bump_api_usage, today_usage_count
from utils.api_key import generate_api_key, sha256_hex
from utils.security import get_current_user_id

agents_router = APIRouter(prefix="/agents", tags=["agents"])
chat_router = APIRouter(prefix="/chat", tags=["chat"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])
public_agent_router = APIRouter(tags=["public-agent"])

_graph = build_agent_app()


def _agents():
    return get_db()["agents"]


def _api_keys():
    return get_db()["api_keys"]


def _chat():
    return get_db()["chat_history"]


def _serialize_agent(agent: dict, *, api_key_plain: Optional[str] = None) -> AgentOut:
    key_doc = get_db()["api_keys"].find_one({"agent_id": str(agent["_id"])})
    prefix = key_doc.get("key_prefix") if key_doc else None
    return AgentOut(
        id=str(agent["_id"]),
        name=agent["name"],
        model_name=agent["model_name"],
        system_prompt=agent["system_prompt"],
        memory_enabled=bool(agent.get("memory_enabled", True)),
        rag_enabled=bool(agent.get("rag_enabled", False)),
        api_key=api_key_plain,
        api_key_prefix=prefix,
        created_at=agent.get("created_at"),
        updated_at=agent.get("updated_at"),
    )


@agents_router.post("", response_model=AgentOut)
async def create_agent(payload: AgentCreate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    agents = _agents()
    keys = _api_keys()

    name = payload.name.strip()
    existing = await run_in_threadpool(lambda: agents.find_one({"user_id": user_id, "name": name}))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have an agent with this name")

    now = datetime.now(timezone.utc)
    agent_doc = {
        "user_id": user_id,
        "name": name,
        "model_name": payload.model_name,
        "system_prompt": payload.system_prompt,
        "memory_enabled": payload.memory_enabled,
        "rag_enabled": payload.rag_enabled,
        "created_at": now,
        "updated_at": now,
    }

    def _insert():
        res = agents.insert_one(agent_doc)
        aid = str(res.inserted_id)
        plain = generate_api_key()
        keys.insert_one(
            {
                "agent_id": aid,
                "user_id": user_id,
                "key_sha256": sha256_hex(plain),
                "key_prefix": plain[:20] + "…",
                "created_at": now,
            }
        )
        inserted = agents.find_one({"_id": res.inserted_id})
        return inserted, plain

    inserted, plain = await run_in_threadpool(_insert)
    out = _serialize_agent(inserted, api_key_plain=plain)
    return out


@agents_router.get("", response_model=list[AgentOut])
async def list_agents(user_id: str = Depends(get_current_user_id)):
    agents = _agents()

    def _list():
        return list(agents.find({"user_id": user_id}).sort("created_at", -1))

    rows = await run_in_threadpool(_list)
    return [_serialize_agent(a) for a in rows]


@agents_router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(agent_id: str, user_id: str = Depends(get_current_user_id)):
    agents = _agents()
    try:
        oid = ObjectId(agent_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id")

    agent = await run_in_threadpool(lambda: agents.find_one({"_id": oid, "user_id": user_id}))
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return _serialize_agent(agent)


@agents_router.patch("/{agent_id}", response_model=AgentOut)
async def update_agent(agent_id: str, payload: AgentUpdate, user_id: str = Depends(get_current_user_id)):
    agents = _agents()
    try:
        oid = ObjectId(agent_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id")

    agent = await run_in_threadpool(lambda: agents.find_one({"_id": oid, "user_id": user_id}))
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    update: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if payload.name is not None:
        update["name"] = payload.name.strip()
    if payload.model_name is not None:
        update["model_name"] = payload.model_name
    if payload.system_prompt is not None:
        update["system_prompt"] = payload.system_prompt
    if payload.memory_enabled is not None:
        update["memory_enabled"] = payload.memory_enabled
    if payload.rag_enabled is not None:
        update["rag_enabled"] = payload.rag_enabled

    if "name" in update and update["name"] != agent["name"]:
        clash = await run_in_threadpool(
            lambda: agents.find_one({"user_id": user_id, "name": update["name"], "_id": {"$ne": oid}})
        )
        if clash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name already in use")

    await run_in_threadpool(lambda: agents.update_one({"_id": oid}, {"$set": update}))
    refreshed = await run_in_threadpool(lambda: agents.find_one({"_id": oid}))
    return _serialize_agent(refreshed)


@agents_router.delete("/{agent_id}")
async def delete_agent(agent_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    agents = _agents()
    try:
        oid = ObjectId(agent_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id")

    agent = await run_in_threadpool(lambda: agents.find_one({"_id": oid, "user_id": user_id}))
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    def _purge():
        agents.delete_one({"_id": oid})
        db["api_keys"].delete_many({"agent_id": agent_id})
        db["chat_history"].delete_many({"agent_id": agent_id})
        db["uploaded_files"].delete_many({"agent_id": agent_id})
        shutil.rmtree(VECTOR_ROOT / agent_id, ignore_errors=True)
        shutil.rmtree(UPLOADS_ROOT / agent_id, ignore_errors=True)

    await run_in_threadpool(_purge)
    return {"status": "deleted"}


@agents_router.post("/{agent_id}/regenerate-key", response_model=AgentOut)
async def regenerate_api_key(agent_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    agents = _agents()
    keys = _api_keys()
    try:
        oid = ObjectId(agent_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id")

    agent = await run_in_threadpool(lambda: agents.find_one({"_id": oid, "user_id": user_id}))
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    now = datetime.now(timezone.utc)
    plain = generate_api_key()

    def _swap():
        keys.delete_many({"agent_id": agent_id})
        keys.insert_one(
            {
                "agent_id": agent_id,
                "user_id": user_id,
                "key_sha256": sha256_hex(plain),
                "key_prefix": plain[:20] + "…",
                "created_at": now,
            }
        )

    await run_in_threadpool(_swap)
    refreshed = await run_in_threadpool(lambda: agents.find_one({"_id": oid}))
    return _serialize_agent(refreshed, api_key_plain=plain)


@dashboard_router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(user_id: str = Depends(get_current_user_id)):
    db = get_db()

    def _counts():
        total = db["agents"].count_documents({"user_id": user_id})
        return total

    total = await run_in_threadpool(_counts)
    usage = await run_in_threadpool(lambda: today_usage_count(db, user_id))
    recent = await run_in_threadpool(lambda: recent_chats_for_user(db["chat_history"], user_id=user_id, limit=8))
    return DashboardStats(total_agents=total, api_calls_today=usage, recent_chats=recent)


@chat_router.post("", response_model=ChatResponse)
@limiter.limit("120/minute")
async def chat_with_agent(
    request: Request,
    payload: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    agents = _agents()
    try:
        oid = ObjectId(payload.agent_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id")

    agent = await run_in_threadpool(lambda: agents.find_one({"_id": oid, "user_id": user_id}))
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    bump_api_usage(db, user_id)

    history: list[dict[str, str]] = []
    if agent.get("memory_enabled", True):
        history = await run_in_threadpool(
            lambda: recent_messages(db["chat_history"], user_id=user_id, agent_id=payload.agent_id, limit=20)
        )

    state = {
        "query": payload.message,
        "agent_id": payload.agent_id,
        "model_name": agent["model_name"],
        "system_prompt": agent["system_prompt"],
        "rag_enabled": bool(agent.get("rag_enabled", False)),
        "memory_enabled": bool(agent.get("memory_enabled", True)),
        "history": history,
        "vector_root": str(VECTOR_ROOT),
    }

    def _run():
        return _graph.invoke(state)

    result = await run_in_threadpool(_run)
    reply = str(result.get("response", "")).strip()

    if agent.get("memory_enabled", True):
        await run_in_threadpool(
            lambda: append_message(
                db["chat_history"],
                user_id=user_id,
                agent_id=payload.agent_id,
                role="user",
                content=payload.message,
            )
        )
        await run_in_threadpool(
            lambda: append_message(
                db["chat_history"],
                user_id=user_id,
                agent_id=payload.agent_id,
                role="assistant",
                content=reply,
            )
        )

    return ChatResponse(
        reply=reply,
        agent_id=payload.agent_id,
        used_rag=bool(agent.get("rag_enabled", False)),
        used_memory=bool(agent.get("memory_enabled", True)),
    )


@public_agent_router.post("/agent/{agent_name}", response_model=ExternalAgentChatResponse)
@limiter.limit("120/minute")
async def public_agent_invoke(
    request: Request,
    agent_name: str,
    body: ExternalAgentChatRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    api_key = x_api_key or request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key header")

    db = get_db()
    digest = sha256_hex(api_key)
    key_doc = await run_in_threadpool(lambda: db["api_keys"].find_one({"key_sha256": digest}))
    if not key_doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    agent_id = key_doc["agent_id"]
    try:
        oid = ObjectId(agent_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Corrupt agent reference")

    agent = await run_in_threadpool(lambda: db["agents"].find_one({"_id": oid}))
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    if agent["name"] != agent_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent name does not match this API key")

    owner_id = agent["user_id"]
    bump_api_usage(db, owner_id)

    history: list[dict[str, str]] = []
    if agent.get("memory_enabled", True):
        history = await run_in_threadpool(
            lambda: recent_messages(db["chat_history"], user_id=owner_id, agent_id=agent_id, limit=20)
        )

    state = {
        "query": body.message,
        "agent_id": agent_id,
        "model_name": agent["model_name"],
        "system_prompt": agent["system_prompt"],
        "rag_enabled": bool(agent.get("rag_enabled", False)),
        "memory_enabled": bool(agent.get("memory_enabled", True)),
        "history": history,
        "vector_root": str(VECTOR_ROOT),
    }

    def _run():
        return _graph.invoke(state)

    result = await run_in_threadpool(_run)
    reply = str(result.get("response", "")).strip()

    if agent.get("memory_enabled", True):
        await run_in_threadpool(
            lambda: append_message(
                db["chat_history"],
                user_id=owner_id,
                agent_id=agent_id,
                role="user",
                content=body.message,
            )
        )
        await run_in_threadpool(
            lambda: append_message(
                db["chat_history"],
                user_id=owner_id,
                agent_id=agent_id,
                role="assistant",
                content=reply,
            )
        )

    return ExternalAgentChatResponse(
        reply=reply,
        agent_name=agent["name"],
        used_rag=bool(agent.get("rag_enabled", False)),
        used_memory=bool(agent.get("memory_enabled", True)),
    )
