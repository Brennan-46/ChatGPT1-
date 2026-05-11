import json
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException
import redis

from app.core.config import settings
from app.metrics import incr


RATE_WINDOW_SECONDS = 60
RATE_MAX_REQUESTS = 30
_REQUESTS: dict[str, deque[float]] = defaultdict(deque)
_redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def _tenant_keys() -> dict[str, dict[str, str]]:
    if not settings.tenant_api_keys_json:
        return {}
    try:
        return json.loads(settings.tenant_api_keys_json)
    except Exception:
        return {}


def enforce_api_key(
    x_api_key: str = Header(default=""),
    x_tenant_id: str = Header(default="default"),
) -> None:
    tenant = x_tenant_id or "default"
    tenant_keys = _tenant_keys()

    if tenant_keys:
        cfg = tenant_keys.get(tenant)
        if not cfg:
            incr("auth_failures_total")
            raise HTTPException(status_code=401, detail="Unknown tenant")
        active = cfg.get("active_key", "")
        next_key = cfg.get("next_key", "")
        if x_api_key not in {active, next_key}:
            incr("auth_failures_total")
            raise HTTPException(status_code=401, detail="Invalid API key")
        return

    # backward compatibility single-key mode
    if settings.api_key and x_api_key != settings.api_key:
        incr("auth_failures_total")
        raise HTTPException(status_code=401, detail="Invalid API key")


def enforce_rate_limit(subject: str) -> None:
    key = f"rl:{subject}"
    now = int(time.time())
    try:
        with _redis_client.pipeline() as pipe:
            pipe.zremrangebyscore(key, 0, now - RATE_WINDOW_SECONDS)
            pipe.zadd(key, {f"{now}:{time.time_ns()}": now})
            pipe.zcard(key)
            pipe.expire(key, RATE_WINDOW_SECONDS + 5)
            _, _, count, _ = pipe.execute()
        if count > RATE_MAX_REQUESTS:
            incr("rate_limit_block_total")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        return
    except Exception:
        if not settings.rate_limiter_fail_open:
            incr("rate_limiter_unavailable_total")
            raise HTTPException(status_code=503, detail="Rate limiter unavailable")

        # dev-only fallback
        q = _REQUESTS[subject]
        while q and time.time() - q[0] > RATE_WINDOW_SECONDS:
            q.popleft()
        if len(q) >= RATE_MAX_REQUESTS:
            incr("rate_limit_block_total")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        q.append(time.time())
