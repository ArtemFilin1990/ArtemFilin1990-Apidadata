"""Rule-based scoring for legal entities using DaData party payload."""
from __future__ import annotations

from datetime import date
from typing import Any


def _safe(data: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
    return default if data is None else data


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(max(low, min(high, round(value))))


def _grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    if score >= 30:
        return "D"
    return "E"


def _decision(grade: str, stop_factor: bool, confidence: str) -> str:
    if stop_factor or grade == "E":
        return "DECLINE"
    if grade == "D" or confidence == "LOW":
        return "REVIEW"
    if grade == "C":
        return "APPROVE_WITH_LIMITS"
    return "APPROVE"


def build_score_report(party: dict) -> dict[str, Any]:
    data = party.get("data") or {}
    today = date.today().isoformat()

    inn = data.get("inn") or ""
    status = _safe(data, "state", "status", default="")

    flags: list[str] = []
    reasons: list[str] = []

    stop_factor = status in {"BANKRUPT", "LIQUIDATED", "LIQUIDATING"}
    if stop_factor:
        flags.append("STOP_STATUS")
        reasons.append("Статус компании указывает на ликвидацию/банкротство")

    # legal
    legal_score = 70.0
    age_months = _to_float(_safe(data, "state", "registration_date"))
    if age_months is not None:
        years = (date.today().toordinal() - date.fromtimestamp(age_months / 1000).toordinal()) / 365.25
        if years < 0.5:
            legal_score -= 25
            reasons.append("Возраст компании менее 6 месяцев")
        elif years < 1:
            legal_score -= 15
            reasons.append("Возраст компании от 6 до 12 месяцев")
        elif years > 3:
            legal_score += 5
            reasons.append("Компания старше 3 лет")

    if _safe(data, "address", "data", "qc") == "5":
        legal_score -= 20
        flags.append("MASS_ADDRESS")
        reasons.append("Признак массового адреса")

    if _safe(data, "management", "disqualified"):
        legal_score -= 20
        flags.append("MANAGER_DISQUALIFIED")
        reasons.append("Руководитель дисквалифицирован")

    # finance
    fin = data.get("finance") or {}
    fin_score = 70.0
    revenue = _to_float(fin.get("revenue"))
    income = _to_float(fin.get("income"))
    debt = _to_float(fin.get("debt"))
    penalty = _to_float(fin.get("penalty"))

    if income is not None and income < 0:
        fin_score -= 20
        reasons.append("Отрицательный финансовый результат")

    if debt is not None and debt > 0:
        fin_score -= 10
        reasons.append("Есть налоговая недоимка")

    if penalty is not None and penalty > 0:
        fin_score -= 10
        reasons.append("Есть налоговые штрафы")

    if revenue is not None and revenue > 0 and debt is not None and debt / revenue > 0.2:
        fin_score -= 20
        flags.append("HIGH_DEBT_TO_REVENUE")
        reasons.append("Высокая доля долга к выручке")

    # courts
    court_score = 80.0
    court_signals = 0
    if _safe(data, "address", "invalidity", "code") == "COURT":
        court_signals += 1
    for founder in data.get("founders") or []:
        if _safe(founder, "invalidity", "code") == "COURT":
            court_signals += 1
    for manager in data.get("managers") or []:
        if _safe(manager, "invalidity", "code") == "COURT":
            court_signals += 1

    if court_signals > 0:
        court_score -= min(40, court_signals * 12)
        flags.append("HAS_ARBITRATION_SIGNALS")
        reasons.append("Обнаружены судебные сигналы по недостоверности")
    else:
        reasons.append("Нет судебных сигналов по недостоверности")

    # enforcement proxy (FSSP missing in current bot)
    enforce_score = 60.0
    missing: list[str] = ["enforcement", "bankruptcy"]
    reasons.append("Нет прямых данных ФССП — скоринг по исполнению с пониженной уверенностью")

    # behavior
    behavior_score = 75.0
    if _safe(data, "address", "unrestricted_value"):
        behavior_score += 5
    if _safe(data, "management", "name"):
        behavior_score += 5
    if _safe(data, "branch_count") and _to_float(_safe(data, "branch_count")) and _to_float(_safe(data, "branch_count")) > 20:
        behavior_score += 5

    if "MASS_ADDRESS" in flags and age_months is not None:
        years = (date.today().toordinal() - date.fromtimestamp(age_months / 1000).toordinal()) / 365.25
        if years < 1:
            behavior_score -= 20
            flags.append("YOUNG_AND_MASS_ADDRESS")
            reasons.append("Комбо-риск: молодая компания с массовым адресом")

    subscores = {
        "legal": _clamp(legal_score),
        "fin": _clamp(fin_score),
        "court": _clamp(court_score),
        "enforce": _clamp(enforce_score),
        "behavior": _clamp(behavior_score),
    }

    score_raw = (
        0.25 * subscores["legal"]
        + 0.25 * subscores["fin"]
        + 0.20 * subscores["court"]
        + 0.20 * subscores["enforce"]
        + 0.10 * subscores["behavior"]
    )

    if stop_factor:
        score = min(_clamp(score_raw), 20)
    else:
        score = _clamp(score_raw)

    # confidence from missing count
    if len(missing) >= 2:
        confidence = "MED"
    else:
        confidence = "HIGH"

    grade = _grade(score)
    decision = _decision(grade, stop_factor, confidence)

    freshness = {
        "registry": today,
        "courts": today,
        "finance": today if fin else "unknown",
        "enforcement": "missing",
    }

    if not fin:
        missing.append("finance")

    # Unique + top 10
    seen = set()
    reasons_top = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            reasons_top.append(reason)
    reasons_top = reasons_top[:10]

    return {
        "inn": inn,
        "score": score,
        "grade": grade,
        "decision": decision,
        "confidence": confidence,
        "flags": list(dict.fromkeys(flags)),
        "subscores": subscores,
        "reasons_top": reasons_top,
        "freshness": freshness,
        "missing": list(dict.fromkeys(missing)),
    }
