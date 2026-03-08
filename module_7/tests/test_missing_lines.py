"""
test_missing_lines.py

Additional tests to improve coverage of rarely executed branches in src.app
and src.clean modules.
"""

import pytest
import psycopg

import src.app as appmod
import src.clean as cleanmod


@pytest.mark.web
def test_app_covers_lock_helpers_and_index_redirect(tmp_path):
    """
    Test lock helpers and root route redirect behavior.

    Covers lock_exists, create_lock, remove_lock, and the "/" redirect.
    """
    original_lock = appmod.LOCK_FILE
    try:
        appmod.LOCK_FILE = tmp_path / "pull.lock"

        assert appmod.lock_exists() is False
        appmod.create_lock()
        assert appmod.lock_exists() is True
        appmod.remove_lock()
        assert appmod.lock_exists() is False

        app = appmod.create_app(
            lock_exists_fn=lambda: False,
            build_blocks_fn=lambda: [],
        )
        client = app.test_client()
        resp = client.get("/")
        assert resp.status_code in (301, 302, 308)
        assert "/analysis" in resp.headers.get("Location", "")
    finally:
        appmod.LOCK_FILE = original_lock


@pytest.mark.buttons
def test_get_conn_uses_env_url_and_update_analysis_not_busy(monkeypatch):
    """
    Test get_conn environment variable path and update-analysis success case.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/module_3db",
    )

    app = appmod.create_app(
        lock_exists_fn=lambda: False,
        build_blocks_fn=lambda: [],
    )
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/update-analysis")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}

    try:
        headers, rows = appmod.fetch_one("SELECT 1;")
        assert headers
        assert rows
    except (psycopg.Error, OSError):
        pytest.skip(
            "DB not available locally for get_conn coverage; "
            "run with Postgres up (or CI)."
        )


@pytest.mark.analysis
def test_clean_module_missing_lines():
    """
    Exercise optional helper functions in src.clean for coverage.
    """
    if hasattr(cleanmod, "format_percent"):
        assert cleanmod.format_percent(0.1234)
        assert isinstance(cleanmod.format_percent(0.1), str)

    if hasattr(cleanmod, "to_float"):
        assert cleanmod.to_float("3.90") is not None
        assert cleanmod.to_float(None) is None
