import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            return

        now = time.monotonic()
        window_start = now - window_seconds

        with self._lock:
            request_times = self._requests[key]
            while request_times and request_times[0] <= window_start:
                request_times.popleft()

            if len(request_times) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        "Too many requests. Please wait a minute before trying again."
                    ),
                )

            request_times.append(now)


rate_limiter = InMemoryRateLimiter()


def rate_limit_by_ip(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(client_ip, settings.rate_limit_per_minute)
