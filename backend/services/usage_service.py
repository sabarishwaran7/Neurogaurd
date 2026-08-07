"""API usage accounting for dashboard metrics."""

from datetime import datetime, timezone

from pymongo.database import Database


def bump_api_usage(db: Database, user_id: str) -> None:
    day = datetime.now(timezone.utc).date().isoformat()
    db["api_usage"].update_one(
        {"user_id": user_id, "day": day},
        {"$inc": {"count": 1}},
        upsert=True,
    )


def today_usage_count(db: Database, user_id: str) -> int:
    day = datetime.now(timezone.utc).date().isoformat()
    doc = db["api_usage"].find_one({"user_id": user_id, "day": day})
    return int(doc.get("count", 0)) if doc else 0
