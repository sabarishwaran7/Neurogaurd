"""NeuroGuard extension routes: history tracking API (file-based, no MongoDB required)."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/neuroguard", tags=["neuroguard"])

# Store history in a JSON file inside the backend directory
_HISTORY_FILE = Path(__file__).resolve().parent.parent / "neuroguard_history.json"
_lock = threading.Lock()
_MAX_ENTRIES = 1000


def _read_history() -> list:
    """Read history from the JSON file."""
    if not _HISTORY_FILE.exists():
        return []
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_history(history: list) -> None:
    """Write history to the JSON file."""
    with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


class HistoryEntry(BaseModel):
    url: str
    domain: str
    status: str  # SAFE | SUSPICIOUS | HARMFUL
    action: str  # ALLOWED | BLOCKED
    serpRisky: Optional[bool] = False
    serpMatchCount: Optional[int] = 0
    explanation: Optional[str] = None
    riskLevel: Optional[str] = None
    durationMs: Optional[int] = 0
    time: Optional[str] = None


@router.post("/history")
async def add_history_entry(entry: HistoryEntry):
    """Add a new browsing activity entry from the Chrome extension."""
    with _lock:
        history = _read_history()

        record = entry.dict()
        if not record.get("time"):
            record["time"] = datetime.now(timezone.utc).strftime("%b %d, %Y, %I:%M:%S %p")

        history.insert(0, record)

        # Cap entries
        if len(history) > _MAX_ENTRIES:
            history = history[:_MAX_ENTRIES]

        _write_history(history)

    return {"status": "ok", "total": len(history)}


@router.get("/history")
async def get_history():
    """Return all browsing history entries."""
    history = _read_history()
    return {"history": history, "total": len(history)}


@router.delete("/history")
async def clear_history():
    """Clear all browsing history."""
    with _lock:
        _write_history([])
    return {"status": "cleared"}


@router.get("/stats")
async def get_stats():
    """Return aggregated stats from the browsing history."""
    history = _read_history()
    total = len(history)
    safe = sum(1 for e in history if e.get("status") == "SAFE")
    suspicious = sum(1 for e in history if e.get("status") == "SUSPICIOUS")
    harmful = sum(1 for e in history if e.get("status") == "HARMFUL")
    blocked = sum(1 for e in history if e.get("action") == "BLOCKED")

    # Unique domains
    domains = set(e.get("domain", "") for e in history)

    return {
        "total_scanned": total,
        "safe": safe,
        "suspicious": suspicious,
        "harmful": harmful,
        "blocked": blocked,
        "unique_domains": len(domains),
    }
