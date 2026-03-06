"""Simple in-memory TTL cache."""
import threading
import time
from typing import Any, Optional


class TTLCache:
    def __init__(self, ttl: int = 3600) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, ts = entry
            if time.time() - ts < self._ttl:
                return value
            del self._store[key]
            return None

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (value, time.time())


party_cache: TTLCache = TTLCache(ttl=3600)
aff_cache: TTLCache = TTLCache(ttl=3600)
