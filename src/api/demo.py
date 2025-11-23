"""Demo activity endpoints for the interactive landing page.

Provides an in-memory store for recent demo events by default. If
`DEMO_STORE=redis` and a reachable `REDIS_URL` is provided, events will
be persisted to Redis (list key `demo:events`) so they survive app
restarts.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import json

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
import logging

router = APIRouter()


class DemoEvent(BaseModel):
    agent: str
    scenario: str
    name: str = "Anonymous"
    city: str = ""
    timestamp: str | None = None


# Simple in-memory store (capped)
_events: List[DemoEvent] = []
_MAX_EVENTS = 200

# Simple in-memory rate limiter: map client_ip -> list[timestamps]
_rate_index: Dict[str, List[datetime]] = {}
_RATE_LIMIT = 10  # max requests
_RATE_WINDOW = timedelta(seconds=60)  # per 60 seconds

# Redis-backed persistence (optional)
_REDIS_ENABLED = False
_redis = None
_REDIS_KEY = "demo:events"

logger = logging.getLogger(__name__)


def _init_redis() -> None:
    """Attempt to initialize redis client if configured."""
    global _REDIS_ENABLED, _redis
    try:
        if os.getenv("DEMO_STORE", "").lower() != "redis":
            return
        redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
        try:
            # Try importing asyncio redis client
            import redis.asyncio as aioredis  # type: ignore

            _redis = aioredis.from_url(redis_url)
            _REDIS_ENABLED = True
            logger.info("Demo persistence: Redis enabled (%s)", redis_url)
        except Exception:
            logger.exception("Failed to initialize redis.asyncio client; falling back to in-memory store")
            _REDIS_ENABLED = False
    except Exception:
        _REDIS_ENABLED = False


# Initialize redis at module import (best-effort)
_init_redis()

# Optional shared secret to prevent spam. If set, clients must send
# header `X-DEMO-KEY` with the same value to record events.
_DEMO_KEY = os.getenv("DEMO_KEY")


@router.post("/demo/record")
async def record_demo(event: DemoEvent, request: Request) -> Dict[str, Any]:
    """Record a demo event.

    The frontend should POST here when a demo completes to add an item to
    the recent activity feed. This endpoint is intentionally lightweight.
    """
    # Basic input validation / sanitization
    agent = (event.agent or "").strip().lower()[:50]
    scenario = (event.scenario or "").strip()[:120]
    name = (event.name or "Anonymous").strip()[:100]
    city = (event.city or "").strip()[:100]

    if not agent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="agent is required")

    # Rate limiting by client IP (best-effort; respects X-Forwarded-For if present)
    xff = request.headers.get("x-forwarded-for")
    client_ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown")

    # If a shared DEMO_KEY is configured, require it in the request header
    if _DEMO_KEY:
        header_key = request.headers.get("x-demo-key") or request.headers.get("X-DEMO-KEY")
        if not header_key or header_key != _DEMO_KEY:
            logger.warning("Missing or invalid demo key for client %s", client_ip)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_demo_key")
    now = datetime.utcnow()
    bucket = _rate_index.setdefault(client_ip, [])
    # prune old timestamps
    cutoff = now - _RATE_WINDOW
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= _RATE_LIMIT:
        logger.warning("Rate limit exceeded for %s", client_ip)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limit_exceeded")
    bucket.append(now)

    event.agent = agent
    event.scenario = scenario
    event.name = name
    event.city = city
    event.timestamp = now.isoformat()

    # If Redis is enabled, push to Redis list and trim
    if _REDIS_ENABLED and _redis is not None:
        try:
            payload = json.dumps(event.dict())
            await _redis.lpush(_REDIS_KEY, payload)
            await _redis.ltrim(_REDIS_KEY, 0, _MAX_EVENTS - 1)
            return {"success": True, "message": "Recorded (redis)", "event": event}
        except Exception:
            logger.exception("Redis write failed; falling back to in-memory store")

    # Prepend to keep newest first (in-memory fallback)
    _events.insert(0, event)
    # Trim store
    if len(_events) > _MAX_EVENTS:
        del _events[_MAX_EVENTS:]
    return {"success": True, "message": "Recorded", "event": event}


@router.get("/demo/recent")
async def recent_demos(limit: int = 6) -> Dict[str, Any]:
    """Return the most recent demo events (newest first)."""
    try:
        l = max(1, min(50, int(limit)))
    except Exception:
        l = 6

    # If Redis enabled, read from Redis list
    if _REDIS_ENABLED and _redis is not None:
        try:
            raw = await _redis.lrange(_REDIS_KEY, 0, l - 1)
            events: List[Dict[str, Any]] = []
            for item in raw:
                try:
                    if isinstance(item, bytes):
                        item = item.decode('utf-8')
                    events.append(json.loads(item))
                except Exception:
                    logger.exception("Failed to parse redis event item")
            return {"events": events}
        except Exception:
            logger.exception("Redis read failed; falling back to in-memory store")

    # Fallback to in-memory
    return {"events": [e.dict() for e in _events[:l]]}
