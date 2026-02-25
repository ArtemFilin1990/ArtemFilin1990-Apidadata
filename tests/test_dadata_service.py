import datetime as dt
"""Tests for DaData service wrappers."""
from unittest.mock import MagicMock

import pytest

from services import dadata_service as ds
from services.cache import aff_cache, party_cache


def setup_function() -> None:
    party_cache._store.clear()  # noqa: SLF001 - acceptable in tests
    aff_cache._store.clear()  # noqa: SLF001 - acceptable in tests


def test_find_party_default_branch_main(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.find_by_id.return_value = [{"value": "ok"}]
    monkeypatch.setattr(ds, "get_client", lambda: mock_client)

    result = ds.find_party("7707083893")

    assert result == {"value": "ok"}
    mock_client.find_by_id.assert_called_once_with("party", "7707083893", branch_type="MAIN")


def test_find_party_passes_supported_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.find_by_id.return_value = [{"value": "ok"}]
    monkeypatch.setattr(ds, "get_client", lambda: mock_client)

    ds.find_party(
        "7707083893",
        count=20,
        kpp="540602001",
        branch_type="BRANCH",
        type="LEGAL",
        status=["ACTIVE"],
    )

    mock_client.find_by_id.assert_called_once_with(
        "party",
        "7707083893",
        count=20,
        kpp="540602001",
        branch_type="BRANCH",
        type="LEGAL",
        status=["ACTIVE"],
    )


def test_find_party_rejects_invalid_count() -> None:
    with pytest.raises(ValueError, match="count must be in range 1..300"):
        ds.find_party("7707083893", count=301)


def test_find_party_rejects_empty_or_too_long_query() -> None:
    with pytest.raises(ValueError, match="query must be non-empty and up to 300 characters"):
        ds.find_party("")

    with pytest.raises(ValueError, match="query must be non-empty and up to 300 characters"):
        ds.find_party("1" * 301)


def test_find_party_cache_key_includes_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.find_by_id.return_value = [{"value": "ok"}]
    monkeypatch.setattr(ds, "get_client", lambda: mock_client)

    ds.find_party("7707083893", branch_type="MAIN")
    ds.find_party("7707083893", branch_type="MAIN")
    ds.find_party("7707083893", branch_type="BRANCH")

    assert mock_client.find_by_id.call_count == 2


def test_clean_resource_returns_none_on_client_error(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.clean.side_effect = RuntimeError("boom")
    monkeypatch.setattr(ds, "get_client", lambda: mock_client)

    assert ds.clean_resource("phone", "+79991234567") is None
    mock_client.clean.assert_called_once_with("phone", "+79991234567")


def test_close_client_logs_and_clears_client(caplog: pytest.LogCaptureFixture) -> None:
    mock_client = MagicMock()
    mock_client.close.side_effect = RuntimeError("close failed")
    ds._client = mock_client  # noqa: SLF001 - testing internal cache mutation

    with caplog.at_level("ERROR"):
        ds.close_client()

    assert ds._client is None
    assert "Failed to close DaData client" in caplog.text


def test_find_affiliated_passes_supported_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.find_affiliated.return_value = [{"value": "ok"}]
    monkeypatch.setattr(ds, "get_client", lambda: mock_client)

    result = ds.find_affiliated("7736207543", count=20, scope=["FOUNDERS"])

    assert result == [{"value": "ok"}]
    mock_client.find_affiliated.assert_called_once_with(
        "7736207543",
        count=20,
        scope=["FOUNDERS"],
    )


def test_find_affiliated_rejects_invalid_query_or_count() -> None:
    with pytest.raises(ValueError, match="query must be non-empty and up to 300 characters"):
        ds.find_affiliated("")

    with pytest.raises(ValueError, match="query must be non-empty and up to 300 characters"):
        ds.find_affiliated("1" * 301)

    with pytest.raises(ValueError, match="count must be in range 1..300"):
        ds.find_affiliated("7736207543", count=301)


def test_find_affiliated_cache_key_includes_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.find_affiliated.return_value = [{"value": "ok"}]
    monkeypatch.setattr(ds, "get_client", lambda: mock_client)

    ds.find_affiliated("7736207543", scope=["FOUNDERS"])
    ds.find_affiliated("7736207543", scope=["FOUNDERS"])
    ds.find_affiliated("7736207543", scope=["MANAGERS"])

    assert mock_client.find_affiliated.call_count == 2


def test_get_client_passes_timeout_when_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Client:
        pass

    created: dict[str, object] = {}

    def _fake_dadata(token: str, secret: str, timeout: float) -> _Client:
        created["token"] = token
        created["secret"] = secret
        created["timeout"] = timeout
        return _Client()

    monkeypatch.setattr(ds, "_client", None)
    monkeypatch.setattr(ds, "Dadata", _fake_dadata)

    client = ds.get_client()

    assert isinstance(client, _Client)
    assert created["token"] == ds.config.DADATA_API_KEY
    assert created["secret"] == ds.config.DADATA_SECRET_KEY
    assert created["timeout"] == ds.config.DADATA_TIMEOUT


def test_get_client_falls_back_without_timeout_for_newer_sdk(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class _Client:
        pass

    calls: list[tuple[tuple, dict]] = []

    def _fake_dadata(*args, **kwargs):
        calls.append((args, kwargs))
        if "timeout" in kwargs:
            raise TypeError("DadataClient.__init__() got an unexpected keyword argument 'timeout'")
        return _Client()

    monkeypatch.setattr(ds, "_client", None)
    monkeypatch.setattr(ds, "Dadata", _fake_dadata)
    monkeypatch.setattr(ds.dadata_settings, "TIMEOUT_SEC", 3.0)


    with caplog.at_level("WARNING"):
        client = ds.get_client()

    assert isinstance(client, _Client)
    assert len(calls) == 2
    assert "timeout" in calls[0][1]
    assert calls[1][1] == {}
    assert ds.dadata_settings.TIMEOUT_SEC == ds.config.DADATA_TIMEOUT
    assert "TIMEOUT_SEC" in caplog.text


def test_check_npd_status_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b'{"status": true, "message": "ok"}'

    monkeypatch.setattr(ds, "urlopen", lambda req, timeout: _Response())

    result = ds.check_npd_status("027714145906", request_date=dt.date(2024, 1, 1))

    assert result == {"status": True, "message": "ok"}


def test_check_npd_status_rejects_empty_inn() -> None:
    with pytest.raises(ValueError, match="inn must be non-empty and up to 300 characters"):
        ds.check_npd_status("")




def test_get_client_reraises_unrelated_type_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_dadata(*args, **kwargs):
        raise TypeError("broken constructor")

    monkeypatch.setattr(ds, "_client", None)
    monkeypatch.setattr(ds, "Dadata", _fake_dadata)

    with pytest.raises(TypeError, match="broken constructor"):
        ds.get_client()
