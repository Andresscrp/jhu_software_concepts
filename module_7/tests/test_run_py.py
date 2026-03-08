"""
test_run_py.py

Tests for src.run, covering main() behavior and __main__ execution.
"""

import runpy

import flask.app
import pytest

from src import run


@pytest.mark.web
def test_run_main_raises_when_db_url_missing(monkeypatch):
    """main() raises RuntimeError when DATABASE_URL is not set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError):
        run.main()


@pytest.mark.web
def test_run_main_calls_app_run(monkeypatch):
    """main() creates the app and calls app.run(debug=True)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    class DummyApp:
        """Fake Flask app that records calls to run()."""

        def __init__(self):
            self.called = False
            self.kwargs = None

        def run(self, **kwargs):
            """Record that run() was called and save arguments."""
            self.called = True
            self.kwargs = kwargs

        def extra_method(self):
            """Extra public method to satisfy pylint."""
            return None

    dummy = DummyApp()
    monkeypatch.setattr(run, "create_app", lambda: dummy)

    run.main()

    assert dummy.called is True
    assert dummy.kwargs == {"debug": True}


@pytest.mark.web
def test_run_py_main_guard_executes_without_blocking(monkeypatch):
    """Running src.run as __main__ does not block execution."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    # Prevent Flask's real .run() from blocking
    monkeypatch.setattr(
        flask.app.Flask,
        "run",
        lambda self, **kwargs: None,
    )

    runpy.run_module("src.run", run_name="__main__")
