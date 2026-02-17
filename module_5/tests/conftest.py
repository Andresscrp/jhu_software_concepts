"""
conftest.py

Shared Pytest fixtures for the Flask application and test client.
"""

import os

import pytest

from src import app as appmod


# Ensures db-marked tests always have a DB URL
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)


@pytest.fixture()
def flask_app():
    """
    Create a Flask app instance configured for testing.

    Returns:
        A Flask app with TESTING enabled and dependency-injected stubs.
    """
    fake_blocks = [
        {
            "title": "Dummy Analysis Block",
            "headers": ["col"],
            "rows": [(1,)],
        }
    ]

    app_instance = appmod.create_app(
        build_blocks_fn=lambda: fake_blocks,
        lock_exists_fn=lambda: False,
        run_pull_fn=lambda: None,
    )
    app_instance.config.update(TESTING=True)
    return app_instance


@pytest.fixture()
def client(test_app):
    """
    Create a Flask test client from the testing app fixture.

    Args:
        test_app: The Flask application instance under test.

    Returns:
        A Flask test client.
    """
    return test_app.test_client()
