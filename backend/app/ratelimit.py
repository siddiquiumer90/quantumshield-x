"""Rate limiting middleware.

In-memory sliding window by client IP. If REDIS_URL is set and the `redis`
package is installed, it is used instead; any Redis failure falls back to
the in-memory limiter rather than breaking requests.
"""
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import RATE_LIMIT_PER_MINUTE, REDIS_URL

_buckets: dict[str, deque] = defaultdict(deque)
_redis = None
if REDIS_URL:
    try:
        import redis  # type: ignore
        _redis = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2)
        _redis.ping()
    except Exception:
        _redis = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in ("/", "/health", "/docs", "/openapi.json"):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        allowed = True
        if _redis is not None:
            try:
                key = f"qs:rl:{ip}"
                pipe = _redis.pipeline()
                pipe.zremrangebyscore(key, 0, now - 60)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, 60)
                count = pipe.execute()[2]
                allowed = count <= RATE_LIMIT_PER_MINUTE
            except Exception:
                allowed = _redis_fallback(ip, now)
        else:
            allowed = _redis_fallback(ip, now)
        if not allowed:
            return JSONResponse(status_code=429,
                                content={"detail": "Rate limit exceeded. Try again shortly."})
        return await call_next(request)


def _redis_fallback(ip: str, now: float) -> bool:
    q = _buckets[ip]
    while q and q[0] < now - 60:
        q.popleft()
    q.append(now)
    return len(q) <= RATE_LIMIT_PER_MINUTE
