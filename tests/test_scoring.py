from services.scoring import build_score_report


def _party(status: str = "ACTIVE") -> dict:
    return {
        "data": {
            "inn": "7707083893",
            "state": {"status": status, "registration_date": 946684800000},
            "finance": {"revenue": 1_000_000, "income": 100_000, "debt": 0, "penalty": 0},
            "management": {"name": "Иванов И.И."},
            "address": {"value": "г. Москва"},
        }
    }


def test_build_score_report_core_fields() -> None:
    report = build_score_report(_party())

    assert report["inn"] == "7707083893"
    assert 0 <= report["score"] <= 100
    assert report["grade"] in {"A", "B", "C", "D", "E"}
    assert report["decision"] in {"APPROVE", "APPROVE_WITH_LIMITS", "REVIEW", "DECLINE"}
    assert set(report["subscores"].keys()) == {"legal", "fin", "court", "enforce", "behavior"}


def test_build_score_report_stop_factor_decline() -> None:
    report = build_score_report(_party(status="LIQUIDATED"))

    assert report["decision"] == "DECLINE"
    assert report["score"] <= 20
    assert "STOP_STATUS" in report["flags"]
