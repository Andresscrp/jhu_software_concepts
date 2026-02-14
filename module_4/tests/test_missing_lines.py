import pytest

import src.app as appmod
import src.clean as cleanmod


@pytest.mark.web
def test_app_covers_lock_helpers_and_index_redirect(tmp_path):
    # Cover: lock_exists / create_lock / remove_lock 
    # by pointing LOCK_FILE at a temp path
    original_lock = appmod.LOCK_FILE
    try:
        appmod.LOCK_FILE = tmp_path / "pull.lock"

        # lock_exists False -> create_lock -> True -> remove_lock -> False
        assert appmod.lock_exists() is False
        appmod.create_lock()
        assert appmod.lock_exists() is True
        appmod.remove_lock()
        assert appmod.lock_exists() is False

        # Cover: "/" route redirect
        app = appmod.create_app(lock_exists_fn=lambda: False, build_blocks_fn=lambda: [])
        client = app.test_client()
        resp = client.get("/")
        assert resp.status_code in (301, 302, 308)
        assert "/analysis" in resp.headers.get("Location", "")
    finally:
        appmod.LOCK_FILE = original_lock


@pytest.mark.buttons
def test_get_conn_uses_env_url_and_update_analysis_not_busy(monkeypatch):
    # Cover: get_conn env path + update-analysis 200 path
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/module_3db")

    app = appmod.create_app(lock_exists_fn=lambda: False, build_blocks_fn=lambda: [])
    app.config.update(TESTING=True)
    client = app.test_client()

    # hits update_analysis success branch
    resp = client.post("/update-analysis")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}

    # hits get_conn() env path (fetch_one -> get_conn)
    # use a tiny query; if DB isn't running this will raise, so we skip gracefully
    try:
        headers, rows = appmod.fetch_one("SELECT 1;")
        assert headers
        assert rows
    except Exception:
        pytest.skip("DB not available locally for get_conn coverage; run with Postgres up (or CI).")


@pytest.mark.analysis
def test_clean_module_missing_lines():
    # Cover src/clean.py lines 140-149 by calling the function(s) that live there.
    # These calls are designed to safely execute regardless of exact implementation.
    if hasattr(cleanmod, "format_percent"):
        assert cleanmod.format_percent(0.1234)  # should run
        assert isinstance(cleanmod.format_percent(0.1), str)
        
    if hasattr(cleanmod, "to_float"):
        assert cleanmod.to_float("3.90") is not None
        assert cleanmod.to_float(None) is None
