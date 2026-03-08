"""
test_app_coverage.py

Extra coverage-focused tests to exercise less common branches in src/app.py.
"""

import types

import pytest

from src import app as appmod


@pytest.mark.web
def test_index_redirects_to_analysis(client):
    """GET / redirects to /analysis."""
    resp = client.get("/")
    assert resp.status_code in (301, 302)
    assert "/analysis" in resp.headers.get("Location", "")


@pytest.mark.web
def test_get_conn_raises_when_no_env_and_no_config(monkeypatch):
    """get_conn raises RuntimeError when DATABASE_URL is not set anywhere."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Ensure we are NOT inside an app context (cfg_url path won't help)
    with pytest.raises(RuntimeError):
        appmod.get_conn()


@pytest.mark.web
def test_get_conn_uses_flask_config_database_url(monkeypatch):
    """get_conn uses current_app.config['DATABASE_URL'] when inside app context."""
    dummy_url = "postgresql://user:pass@localhost:5432/db"

    class DummyConn:
        """Minimal context-manager connection object used for monkeypatching."""

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_connect(url):
        assert url == dummy_url
        return DummyConn()

    monkeypatch.setattr(appmod.psycopg, "connect", fake_connect)

    app = appmod.create_app(
        build_blocks_fn=lambda: [],
        lock_exists_fn=lambda: False,
        run_pull_fn=lambda: None,
    )
    app.config["DATABASE_URL"] = dummy_url

    with app.app_context():
        conn = appmod.get_conn()
        assert conn is not None


@pytest.mark.web
def test_fetch_one_executes_and_returns_headers_and_rows(monkeypatch):
    """fetch_one returns headers from cursor.description and rows from fetchall()."""

    class FakeCursor:
        """Fake cursor capturing execute() inputs and returning one row."""

        def __init__(self):
            self.description = [
                types.SimpleNamespace(name="col1"),
                types.SimpleNamespace(name="col2"),
            ]
            self._sql = None
            self._params = None

        def execute(self, sql, params):
            """Store SQL and parameters passed to execute()."""
            self._sql = sql
            self._params = params

        def fetchall(self):
            """Return a fixed row regardless of SQL or parameters."""
            return [(1, 2)]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeConn:
        """Fake connection that provides a FakeCursor via cursor()."""

        def cursor(self):
            """Return a new FakeCursor instance."""
            return FakeCursor()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_get_conn():
        return FakeConn()

    monkeypatch.setattr(appmod, "get_conn", fake_get_conn)

    headers, rows = appmod.fetch_one("select 1", {"x": 1})
    assert headers == ["col1", "col2"]
    assert rows == [(1, 2)]


@pytest.mark.integration
def test_run_pull_pipeline_calls_subprocess_and_clears_lock(monkeypatch):
    """run_pull_pipeline creates lock, runs pipeline commands, then removes lock."""
    calls = []

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

    run_calls = [c for c in calls if isinstance(c, tuple) and c[0] == "run"]
    assert len(run_calls) == 3


from unittest.mock import MagicMock

import pytest

import src.app as appmod


def _make_client(monkeypatch):
    # Make "not busy" path happen
    if hasattr(appmod, "lock_exists_fn"):
        monkeypatch.setattr(appmod, "lock_exists_fn", lambda: False)
    else:
        # If your code checks LOCK_FILE.exists() indirectly, this makes it false.
        # (harmless if unused)
        monkeypatch.setattr(appmod, "LOCK_FILE", MagicMock(exists=lambda: False), raising=False)

    flask_app = appmod.create_app()
    return flask_app.test_client()


def test_pull_data_calls_publish_task(monkeypatch):
    mock_pub = MagicMock()
    monkeypatch.setattr(appmod, "publish_task", mock_pub)

    client = _make_client(monkeypatch)

    resp = client.post("/pull-data")
    assert resp.status_code == 202
    mock_pub.assert_called_once_with("scrape_new_data", payload={})


def test_update_analysis_calls_publish_task(monkeypatch):
    mock_pub = MagicMock()
    monkeypatch.setattr(appmod, "publish_task", mock_pub)

    client = _make_client(monkeypatch)

    resp = client.post("/update-analysis")
    assert resp.status_code == 202
    mock_pub.assert_called_once_with("recompute_analytics", payload={})


def test_main_reads_env_and_calls_run(monkeypatch):
    # Force env parsing lines 702-704 to execute predictably
    monkeypatch.setenv("FLASK_HOST", "127.0.0.1")
    monkeypatch.setenv("FLASK_PORT", "9999")
    monkeypatch.setenv("FLASK_DEBUG", "no")  # should become False

    fake_flask = MagicMock()
    fake_flask.run = MagicMock()

    monkeypatch.setattr(appmod, "create_app", lambda: fake_flask)

    appmod.main()

    fake_flask.run.assert_called_once_with(host="127.0.0.1", port=9999, debug=False)
