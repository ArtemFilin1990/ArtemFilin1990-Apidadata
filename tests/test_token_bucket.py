"""Tests for the TokenBucket rate limiter in dadata_bot.services.dadata_service."""
import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root is on sys.path so we can import dadata_bot as a package
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies before importing the module under test
sys.modules.setdefault("loguru", MagicMock())
sys.modules.setdefault("cachetools", MagicMock())
sys.modules.setdefault("dotenv", MagicMock())
sys.modules.setdefault("aiohttp", MagicMock())

from dadata_bot.services.dadata_service import TokenBucket  # noqa: E402


@pytest.mark.asyncio
async def test_acquire_immediate_when_tokens_available():
    """acquire() returns immediately when tokens are available."""
    bucket = TokenBucket(rate=10.0, capacity=10.0)
    start = time.monotonic()
    await bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed < 0.1, "acquire() should not block when tokens are available"


@pytest.mark.asyncio
async def test_acquire_does_not_hold_lock_during_sleep():
    """Sleep must happen outside the lock so other coroutines are not blocked."""
    bucket = TokenBucket(rate=1.0, capacity=1.0)
    # Exhaust the only token
    await bucket.acquire()

    lock_acquired_by_other = asyncio.Event()

    async def probe_lock():
        """Try to acquire the lock while the first coroutine is sleeping."""
        # Small delay to let the other coroutine enter acquire() and start sleeping
        await asyncio.sleep(0.05)
        # If the lock is free (sleep is outside the lock), this should succeed quickly
        async with bucket._lock:
            lock_acquired_by_other.set()

    # Launch acquire (which needs to sleep ~1s) and the probe concurrently
    task_acquire = asyncio.create_task(bucket.acquire())
    task_probe = asyncio.create_task(probe_lock())

    # The probe should succeed well before acquire finishes sleeping
    await asyncio.wait_for(task_probe, timeout=0.5)
    assert lock_acquired_by_other.is_set(), "Lock should be released during sleep"

    task_acquire.cancel()
    try:
        await task_acquire
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_acquire_waits_when_no_tokens():
    """acquire() sleeps and retries when bucket is exhausted."""
    bucket = TokenBucket(rate=100.0, capacity=1.0)
    await bucket.acquire()  # exhaust the only token

    start = time.monotonic()
    await bucket.acquire()  # should wait ~0.01s for a refill
    elapsed = time.monotonic() - start
    assert elapsed < 0.5, "Should refill quickly with rate=100"
