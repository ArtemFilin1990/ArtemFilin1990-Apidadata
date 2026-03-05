import asyncio
import hashlib
import json
import os
import time
from datetime import timedelta

import aiohttp
from cachetools import TTLCache
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

DADATA_API_KEY = os.getenv("DADATA_API_KEY")
DADATA_SECRET_KEY = os.getenv("DADATA_SECRET_KEY")


class TokenBucket:
    """Simple async token-bucket rate limiter."""

    def __init__(self, rate: float = 10.0, capacity: float = 10.0):
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        while True:
            wait_time = 0.0
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last
                self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                self._last = now

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

                # Compute wait time but do NOT sleep inside the lock
                wait_time = (1.0 - self._tokens) / self.rate

            if wait_time > 0:
                await asyncio.sleep(wait_time)


class DaDataService:
    # Suggestions API (findById, findAffiliated)
    SUGGESTIONS_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
    # Cleaner API (clean/phone, clean/passport, clean/vehicle)
    CLEANER_URL = "https://cleaner.dadata.ru/api/v1/clean"

    def __init__(self):
        if not DADATA_API_KEY or not DADATA_SECRET_KEY:
            logger.error("DADATA_API_KEY or DADATA_SECRET_KEY not set.")
            raise ValueError("DaData API keys are not configured.")

        self.suggestions_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {DADATA_API_KEY}",
        }
        self.cleaner_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {DADATA_API_KEY}",
            "X-Secret": DADATA_SECRET_KEY,
        }

        self.session: aiohttp.ClientSession | None = None
        self.bucket = TokenBucket(rate=10, capacity=10)

        self.company_cache = TTLCache(maxsize=1000, ttl=timedelta(days=7).total_seconds())
        self.affiliated_cache = TTLCache(maxsize=1000, ttl=timedelta(days=7).total_seconds())
        self.clean_cache = TTLCache(maxsize=1000, ttl=timedelta(hours=24).total_seconds())

    def _get_session(self) -> aiohttp.ClientSession:
        """Return the aiohttp session, creating it lazily inside the event loop."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    # ------------------------------------------------------------------ #
    #  Low-level request with retry + backoff                            #
    # ------------------------------------------------------------------ #
    async def _request(self, url: str, data, headers: dict,
                       cache_key: str | None = None, cache: TTLCache | None = None):
        if cache_key and cache and cache_key in cache:
            logger.debug(f"Cache hit: {cache_key}")
            return cache[cache_key]

        await self.bucket.acquire()

        retries = 0
        max_retries = 3
        backoff = 0.5

        while retries < max_retries:
            try:
                async with self._get_session().post(url, headers=headers,
                                             data=json.dumps(data)) as resp:
                    if resp.status == 200:
                        try:
                            result = await resp.json(content_type=None)
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.error(f"DaData JSON decode error on {url}: {e}")
                            return None
                        if cache_key and cache is not None:
                            cache[cache_key] = result
                        return result
                    if resp.status == 429 or resp.status >= 500:
                        logger.warning(f"DaData {resp.status} on {url}. Retry in {backoff}s")
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        retries += 1
                        continue
                    text = await resp.text()
                    logger.error(f"DaData {resp.status}: {text}")
                    return None
            except aiohttp.ClientError as exc:
                logger.error(f"HTTP error: {exc}")
                retries += 1
                await asyncio.sleep(backoff)
                backoff *= 2

        logger.error(f"Failed after {max_retries} retries: {url}")
        return None

    # ------------------------------------------------------------------ #
    #  Suggestions API                                                    #
    # ------------------------------------------------------------------ #
    async def find_party_by_id(self, query: str):
        url = f"{self.SUGGESTIONS_URL}/findById/party"
        data = {"query": query, "branch_type": "MAIN"}
        cache_key = f"company:{query}"
        return await self._request(url, data, self.suggestions_headers,
                                   cache_key, self.company_cache)

    async def find_branches(self, query: str):
        url = f"{self.SUGGESTIONS_URL}/findById/party"
        data = {"query": query, "branch_type": "BRANCH"}
        cache_key = f"branches:{query}"
        return await self._request(url, data, self.suggestions_headers,
                                   cache_key, self.company_cache)

    async def find_affiliated(self, inn: str):
        """findAffiliated/party — one INN per call."""
        url = f"{self.SUGGESTIONS_URL}/findAffiliated/party"
        data = {"query": inn}
        cache_key = f"aff:{inn}"
        return await self._request(url, data, self.suggestions_headers,
                                   cache_key, self.affiliated_cache)

    async def find_affiliated_multi(self, inn_list: list[str], limit: int = 3):
        """Call findAffiliated for up to `limit` INNs, merge results."""
        results: list[dict] = []
        for inn in inn_list[:limit]:
            resp = await self.find_affiliated(inn)
            if resp and resp.get("suggestions"):
                results.extend(resp["suggestions"])
        return {"suggestions": results}

    async def find_address_by_id(self, fias_id: str):
        url = f"{self.SUGGESTIONS_URL}/findById/address"
        data = {"query": fias_id}
        cache_key = f"address:{fias_id}"
        return await self._request(url, data, self.suggestions_headers,
                                   cache_key, self.company_cache)

    async def find_bank_by_id(self, bic_or_inn: str):
        url = f"{self.SUGGESTIONS_URL}/findById/bank"
        data = {"query": bic_or_inn}
        cache_key = f"bank:{bic_or_inn}"
        return await self._request(url, data, self.suggestions_headers,
                                   cache_key, self.company_cache)

    # ------------------------------------------------------------------ #
    #  Cleaner API  (https://cleaner.dadata.ru/api/v1/clean/*)           #
    # ------------------------------------------------------------------ #
    async def clean_phone(self, phone: str):
        url = f"{self.CLEANER_URL}/phone"
        data = [phone]
        cache_key = f"clean:phone:{hashlib.sha256(phone.encode()).hexdigest()}"
        return await self._request(url, data, self.cleaner_headers,
                                   cache_key, self.clean_cache)

    async def clean_passport(self, passport: str):
        url = f"{self.CLEANER_URL}/passport"
        data = [passport]
        cache_key = f"clean:passport:{hashlib.sha256(passport.encode()).hexdigest()}"
        return await self._request(url, data, self.cleaner_headers,
                                   cache_key, self.clean_cache)

    async def clean_vehicle(self, vehicle: str):
        url = f"{self.CLEANER_URL}/vehicle"
        data = [vehicle]
        cache_key = f"clean:vehicle:{hashlib.sha256(vehicle.encode()).hexdigest()}"
        return await self._request(url, data, self.cleaner_headers,
                                   cache_key, self.clean_cache)

    # ------------------------------------------------------------------ #
    async def close_session(self):
        if self.session is not None and not self.session.closed:
            await self.session.close()
