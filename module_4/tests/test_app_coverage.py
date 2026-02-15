import types
import pytest

from src import app as appmod



@pytest.mark.web
def test_index_redirects_to_analysis(client):
    # Covers the "/" route (often missed)
    resp = client.get("/")
    assert resp.status_code in (301, 302)
    assert "/analysis" in resp.headers.get("Location", "")


@pytest.mark.web
def test_get_conn_raises_when_no_env_and_no_config(monkeypatch):
    # Covers app.py line ~277: RuntimeError when no DATABASE_URL anywhere
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Ensure we are NOT inside an app context (cfg_url path won't help)
    with pytest.raises(RuntimeError):
        appmod.get_conn()


@pytest.mark.web
def test_get_conn_uses_flask_config_database_url(monkeypatch):
    # Covers the "cfg_url" branch (try/except current_app + config path)
    dummy_url = "postgresql://user:pass@localhost:5432/db"

    class DummyConn:
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_connect(url):
        assert url == dummy_url
        return DummyConn()

    monkeypatch.setattr(appmod.psycopg, "connect", fake_connect)

    app = appmod.create_app(build_blocks_fn=lambda: [], lock_exists_fn=lambda: False, run_pull_fn=lambda: None)
    app.config["DATABASE_URL"] = dummy_url

    with app.app_context():
        conn = appmod.get_conn()
        assert conn is not None


@pytest.mark.web
def test_fetch_one_executes_and_returns_headers_and_rows(monkeypatch):
    # Covers app.py lines ~302-313 (fetch_one body: cursor, execute, fetchall, headers)
    class FakeCursor:
        def __init__(self):
            self.description = [types.SimpleNamespace(name="col1"), types.SimpleNamespace(name="col2")]
        def execute(self, sql, params): 
            self._sql = sql
            self._params = params
        def fetchall(self):
            return [(1, 2)]
        def __enter__(self): return self
        def __exit__(self, *args): return False

    class FakeConn:
        def cursor(self): return FakeCursor()
        def __enter__(self): return self
        def __exit__(self, *args): return False

    monkeypatch.setattr(appmod, "get_conn", lambda: FakeConn())

    headers, rows = appmod.fetch_one("select 1", {"x": 1})
    assert headers == ["col1", "col2"]
    assert rows == [(1, 2)]


@pytest.mark.integration
def test_run_pull_pipeline_calls_subprocess_and_clears_lock(monkeypatch):
    # Covers app.py lines ~581-596 (run_pull_pipeline)
    calls = []

    # Don’t touch real lock file / subprocess
    monkeypatch.setattr(appmod, "create_lock", lambda: calls.append("create_lock"))
    monkeypatch.setattr(appmod, "remove_lock", lambda: calls.append("remove_lock"))

    def fake_run(cmd, check):
        calls.append(("run", cmd, check))
        return 0

    monkeypatch.setattr(appmod.subprocess, "run", fake_run)

    # Force scrape.py and clean.py to look like they exist
    monkeypatch.setattr(appmod.Path, "exists", lambda self: True)

    appmod.run_pull_pipeline()

    assert calls[0] == "create_lock"
    assert calls[-1] == "remove_lock"
    # should have run 3 subprocess calls (scrape, clean, load_data)
    run_calls = [c for c in calls if isinstance(c, tuple) and c[0] == "run"]
    assert len(run_calls) == 3
