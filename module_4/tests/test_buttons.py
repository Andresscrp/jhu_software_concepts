import pytest
import src.app as appmod


@pytest.mark.buttons
def test_post_pull_data_returns_202_when_not_busy(monkeypatch):
    """POST /pull-data returns 202 with ok when not busy."""
    monkeypatch.setattr(appmod, "lock_exists", lambda: False)

    started = {"v": False}

    class FakeThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            started["v"] = True

    monkeypatch.setattr(appmod.threading, "Thread", FakeThread)

    app = appmod.create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/pull-data")
    assert resp.status_code == 202
    assert resp.get_json() == {"ok": True}
    assert started["v"] is True


@pytest.mark.buttons
def test_post_update_analysis_returns_200_when_not_busy(monkeypatch):
    """POST /update-analysis returns 200 when not busy."""
    app = appmod.create_app(lock_exists_fn=lambda: False)
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/update-analysis")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}


@pytest.mark.buttons
def test_busy_gating_update_analysis_returns_409(monkeypatch):
    """When busy, POST /update-analysis returns 409 with busy=true."""
    app = appmod.create_app(lock_exists_fn=lambda: True)
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/update-analysis")
    assert resp.status_code == 409
    assert resp.get_json() == {"busy": True}


@pytest.mark.buttons
def test_busy_gating_pull_data_returns_409(monkeypatch):
    """When busy, POST /pull-data returns 409 with busy=true."""
    app = appmod.create_app(lock_exists_fn=lambda: True)
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/pull-data")
    assert resp.status_code == 409
    assert resp.get_json() == {"busy": True}
