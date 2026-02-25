"""DaData API wrapper with caching."""
import json
import logging
from datetime import date
from typing import Any, Literal, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dadata import Dadata

import config
from services.cache import aff_cache, party_cache

logger = logging.getLogger(__name__)


NPD_STATUS_URL = "https://statusnpd.nalog.ru/api/v1/tracker/taxpayer_status"

_client: Optional[Dadata] = None

BranchType = Literal["MAIN", "BRANCH"]
PartyType = Literal["LEGAL", "INDIVIDUAL"]
PartyStatus = Literal["ACTIVE", "LIQUIDATING", "LIQUIDATED", "BANKRUPT", "REORGANIZING"]
AffiliatedScope = Literal["FOUNDERS", "MANAGERS"]


def _party_cache_key(query: str, **kwargs: object) -> str:
    """Build stable cache key for find_party query + filters."""
    payload = {"query": query, **kwargs}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _affiliated_cache_key(query: str, **kwargs: object) -> str:
    """Build stable cache key for find_affiliated query + filters."""
    payload = {"query": query, **kwargs}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def get_client() -> Dadata:
    global _client
    if _client is None:
        try:
            _client = Dadata(
                config.DADATA_API_KEY,
                config.DADATA_SECRET_KEY,
                timeout=config.DADATA_TIMEOUT,
            )
        except TypeError:
            logger.warning(
                "Installed dadata client does not support 'timeout' init argument; "
                "falling back to default client timeout"
            )
            _client = Dadata(config.DADATA_API_KEY, config.DADATA_SECRET_KEY)
    return _client


def close_client() -> None:
    global _client
    client = _client
    if client is None:
        return

    _client = None
    try:
        client.close()
    except Exception:
        logger.exception("Failed to close DaData client")


def find_party(
    query: str,
    *,
    count: int | None = None,
    kpp: str | None = None,
    branch_type: BranchType | None = "MAIN",
    type: PartyType | None = None,
    status: list[PartyStatus] | None = None,
) -> Optional[dict]:
    if not query or len(query) > 300:
        raise ValueError("query must be non-empty and up to 300 characters")

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
    if status:
        params["status"] = status

    cache_key = _party_cache_key(query, **params)
    cached = party_cache.get(cache_key)
    if cached is not None:
        return cached

    result: list[dict] = get_client().find_by_id("party", query, **params)
    if result:
        party_cache.set(cache_key, result[0])
        return result[0]
    return None


def find_affiliated(
    query: str,
    *,
    count: int | None = None,
    scope: list[AffiliatedScope] | None = None,
) -> list[dict]:
    if not query or len(query) > 300:
        raise ValueError("query must be non-empty and up to 300 characters")

    if count is not None and not (1 <= count <= 300):
        raise ValueError("count must be in range 1..300")

    params: dict[str, object] = {}
    if count is not None:
        params["count"] = count
    if scope:
        params["scope"] = scope

    cache_key = _affiliated_cache_key(query, **params)
    cached = aff_cache.get(cache_key)
    if cached is not None:
        return cached

    result: list[dict] = get_client().find_affiliated(query, **params) or []
    aff_cache.set(cache_key, result)
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


def check_npd_status(inn: str, request_date: date | None = None) -> Optional[dict]:
    """Check NPD (self-employed) status via official FNS public API."""
    if not inn or len(inn) > 300:
        raise ValueError("inn must be non-empty and up to 300 characters")

    date_value = (request_date or date.today()).isoformat()
    payload = json.dumps({"inn": inn, "requestDate": date_value}, ensure_ascii=False).encode("utf-8")
    req = Request(
        NPD_STATUS_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=config.DADATA_TIMEOUT) as response:  # nosec B310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except (HTTPError, URLError, TimeoutError, ValueError):
        logger.exception("FNS NPD status check failed for inn=%s", inn)
        return None
