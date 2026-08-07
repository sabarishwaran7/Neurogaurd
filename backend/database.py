import os
from typing import Optional

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

load_dotenv()

_client: Optional[MongoClient] = None


def get_mongo_uri() -> str:
    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        raise RuntimeError("MONGO_URI is not set in the environment.")
    return uri


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(get_mongo_uri(), serverSelectionTimeoutMS=8000)
    return _client


def get_db() -> Database:

    db_name = os.getenv("MONGO_DB", "agentic_platform").strip()
    return get_client()[db_name]


def ensure_indexes() -> None:
    db = get_db()
    users: Collection = db["users"]
    users.create_index([("email", ASCENDING)], unique=True)

    agents: Collection = db["agents"]
    agents.create_index([("user_id", ASCENDING), ("name", ASCENDING)], unique=True)

    chat_history: Collection = db["chat_history"]
    chat_history.create_index([("user_id", ASCENDING), ("agent_id", ASCENDING), ("created_at", ASCENDING)])

    uploaded_files: Collection = db["uploaded_files"]
    uploaded_files.create_index([("agent_id", ASCENDING), ("created_at", ASCENDING)])

    api_keys: Collection = db["api_keys"]
    api_keys.create_index([("key_sha256", ASCENDING)], unique=True)
    api_keys.create_index([("agent_id", ASCENDING)], unique=True)

    api_usage: Collection = db["api_usage"]
    api_usage.create_index([("user_id", ASCENDING), ("day", ASCENDING)], unique=True)


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
