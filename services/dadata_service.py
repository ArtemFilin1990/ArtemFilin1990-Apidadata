"""DaData API wrapper with caching."""
import json
import logging
from typing import Any, Literal, Optional

from dadata import Dadata

import config
from services.cache import aff_cache, party_cache

logger = logging.getLogger(__name__)

_client: Optional[Dadata] = None

BranchType = Literal["MAIN", "BRANCH"]
PartyType = Literal["LEGAL", "INDIVIDUAL"]


def _party_cache_key(query: str, **kwargs: object) -> str:
    """Build stable cache key for find_party query + filters."""
    payload = {"query": query, **kwargs}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def get_client() -> Dadata:
    global _client
    if _client is None:
        _client = Dadata(
            config.DADATA_API_KEY,
            config.DADATA_SECRET_KEY,
            timeout=config.DADATA_TIMEOUT,
        )
    return _client


def close_client() -> None:
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None


def find_party(
    query: str,
    *,
    count: int | None = None,
    kpp: str | None = None,
    branch_type: BranchType | None = "MAIN",
    type: PartyType | None = None,
) -> Optional[dict]:
    if count is not None and not (1 <= count <= 300):
        raise ValueError("count must be in range 1..300")

    params: dict[str, object] = {}
    if count is not None:
        params["count"] = count
    if kpp:
        params["kpp"] = kpp
    if branch_type is not None:
        params["branch_type"] = branch_type
    if type is not None:
        params["type"] = type

    cache_key = _party_cache_key(query, **params)
    cached = party_cache.get(cache_key)
    if cached is not None:
        return cached

    result: list[dict] = get_client().find_by_id("party", query, **params)
    if result:
        party_cache.set(cache_key, result[0])
        return result[0]
    return None


def find_affiliated(inn: str) -> list[dict]:
    cached = aff_cache.get(inn)
    if cached is not None:
        return cached
    result: list[dict] = get_client().find_affiliated(inn) or []
    aff_cache.set(inn, result)
    return result


def find_fns_unit(code: str) -> Optional[dict]:
    try:
        result = get_client().find_by_id("fns_unit", code)
        if result:
            return result[0]
    except Exception:
        logger.exception("DaData find_fns_unit error for code %s", code)
    return None


def find_bank(query: str) -> Optional[dict]:
    try:
        result = get_client().find_by_id("bank", query)
        if result:
            return result[0]
    except Exception:
        logger.exception("DaData find_bank error for query %s", query)
    return None


def clean_resource(resource: str, source: str) -> Optional[Any]:
    try:
        return get_client().clean(resource, source)
    except Exception:
        logger.exception("DaData clean error for resource=%s", resource)
        return None


# ── suggest ──────────────────────────────────────────────────────────────────

def suggest_party(query: str, count: int = 5) -> list[dict]:
    try:
        return get_client().suggest("party", query, count=count) or []
    except Exception:
        logger.exception("DaData suggest_party error for query %s", query)
        return []


def suggest_address(query: str, count: int = 5) -> list[dict]:
    try:
        return get_client().suggest("address", query, count=count) or []
    except Exception:
        logger.exception("DaData suggest_address error for query %s", query)
        return []


def suggest_fio(query: str, count: int = 5) -> list[dict]:
    try:
        return get_client().suggest("fio", query, count=count) or []
    except Exception:
        logger.exception("DaData suggest_fio error for query %s", query)
        return []


# ── clean extras ─────────────────────────────────────────────────────────────

def clean_name(source: str) -> Optional[dict]:
    try:
        return get_client().clean("name", source)
    except Exception:
        logger.exception("DaData clean_name error for %s", source)
        return None


def clean_passport(source: str) -> Optional[dict]:
    try:
        return get_client().clean("passport", source)
    except Exception:
        logger.exception("DaData clean_passport error for %s", source)
        return None


# ── geo ──────────────────────────────────────────────────────────────────────

def geolocate_address(lat: float, lon: float, count: int = 5) -> list[dict]:
    try:
        return get_client().geolocate("address", lat, lon, count=count) or []
    except Exception:
        logger.exception("DaData geolocate error for %s, %s", lat, lon)
        return []


def iplocate(ip: str) -> Optional[dict]:
    try:
        return get_client().iplocate(ip)
    except Exception:
        logger.exception("DaData iplocate error for %s", ip)
        return None


# ── profile ──────────────────────────────────────────────────────────────────

def get_balance() -> Optional[float]:
    try:
        return get_client().get_balance()
    except Exception:
        logger.exception("DaData get_balance error")
        return None


def get_daily_stats() -> Optional[dict]:
    try:
        return get_client().get_daily_stats()
    except Exception:
        logger.exception("DaData get_daily_stats error")
        return None
