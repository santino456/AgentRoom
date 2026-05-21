import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request


class MemoryRateLimiter:
    """基于内存的滑动窗口速率限制器。"""

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        # 清理窗口外的过期记录
        window = self._requests[key]
        cutoff = now - window_seconds
        self._requests[key] = [t for t in window if t > cutoff]
        if len(self._requests[key]) >= limit:
            return False
        self._requests[key].append(now)
        return True


limiter = MemoryRateLimiter()


def rate_limit(key_fn: Callable[[Request], str], limit: int, window_seconds: int):
    """FastAPI dependency factory for rate limiting."""

    def _check(request: Request):
        key = key_fn(request)
        if not limiter.is_allowed(key, limit, window_seconds):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} requests per {window_seconds}s",
            )

    return _check
