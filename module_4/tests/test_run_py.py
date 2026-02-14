import pytest
import runpy


@pytest.mark.web
def test_run_main_raises_when_db_url_missing(monkeypatch):
    import src.run as run
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError):
        run.main()


@pytest.mark.web
def test_run_main_calls_app_run(monkeypatch):
    import src.run as run

    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    class DummyApp:
        def __init__(self):
            self.called = False
            self.kwargs = None

        def run(self, **kwargs):
            self.called = True
            self.kwargs = kwargs

    dummy = DummyApp()
    monkeypatch.setattr(run, "create_app", lambda: dummy)

    run.main()

    assert dummy.called is True
    assert dummy.kwargs == {"debug": True}


@pytest.mark.web
def test_run_py_main_guard_executes_without_blocking(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    # Prevent Flask's real .run() from blocking if src.run triggers it
    import flask.app
    monkeypatch.setattr(flask.app.Flask, "run", lambda self, **kwargs: None)

    runpy.run_module("src.run", run_name="__main__")
