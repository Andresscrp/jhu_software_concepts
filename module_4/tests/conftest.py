"""
conftest.py

Shared pytest fixtures for the Module 4 test suite.

Provides a Flask test client that does not touch the network or database
(by monkeypatching build_blocks and lock_exists).
"""

import pytest
import src.app as appmod


def _fake_blocks():
    """Return deterministic blocks so /analysis can render without Postgres."""
    return [{
        "title": "Q1) Fake",
        "headers": ["col"],
        "rows": [(1,)],
    }]


@pytest.fixture
def client(monkeypatch):
    """
    Create a Flask test client with DB/network work patched out.

    This makes /analysis return 200 consistently in tests.
    """
    monkeypatch.setattr(appmod, "build_blocks", _fake_blocks)
    monkeypatch.setattr(appmod, "lock_exists", lambda: False)

    app = appmod.create_app()
    app.config.update(TESTING=True)
    return app.test_client()
