"""
test_buttons.py

Tests for POST button endpoints in the Flask application.
"""

import pytest

from src import app as appmod


@pytest.mark.buttons
def test_post_pull_data_returns_202_when_not_busy(monkeypatch):
    """POST /pull-data returns 202 with ok=true when no pull is in progress."""
    monkeypatch.setattr(appmod, "lock_exists", lambda: False)

    started = {"v": False}

    class FakeThread:
        """
        Fake thread class used to verify that background execution is triggered.
        """

        def __init__(self, *args, **kwargs):
            """Initialize the fake thread (arguments are ignored)."""
            self.args = args
            self.kwargs = kwargs

        def start(self):
            """Mark the thread as started."""
            started["v"] = True

        def is_alive(self):
            """Extra public method to satisfy pylint."""
            return False

    monkeypatch.setattr(appmod.threading, "Thread", FakeThread)

    app = appmod.create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/pull-data")
    assert resp.status_code == 202
    assert resp.get_json() == {"ok": True}
    assert started["v"] is True


@pytest.mark.buttons
def test_post_update_analysis_returns_200_when_not_busy():
    """POST /update-analysis returns 200 when no pull is in progress."""
    app = appmod.create_app(lock_exists_fn=lambda: False)
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/update-analysis")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}


@pytest.mark.buttons
def test_busy_gating_update_analysis_returns_409():
    """POST /update-analysis returns 409 with busy=true when a pull is running."""
    app = appmod.create_app(lock_exists_fn=lambda: True)
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/update-analysis")
    assert resp.status_code == 409
    assert resp.get_json() == {"busy": True}


@pytest.mark.buttons
def test_busy_gating_pull_data_returns_409():
    """POST /pull-data returns 409 with busy=true when a pull is running."""
    app = appmod.create_app(lock_exists_fn=lambda: True)
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.post("/pull-data")
    assert resp.status_code == 409
    assert resp.get_json() == {"busy": True}
