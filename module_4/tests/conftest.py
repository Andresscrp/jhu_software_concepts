import os
import pytest

from src import app as appmod

# Ensures db-marked tests always have a DB URL
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)

@pytest.fixture()
def app():
    fake_blocks = [{
        "title": "Dummy Analysis Block",
        "headers": ["col"],
        "rows": [(1,)],
    }]

    app = appmod.create_app(
        build_blocks_fn=lambda: fake_blocks,
        lock_exists_fn=lambda: False,
        run_pull_fn=lambda: None,
    )
    app.config.update(TESTING=True)
    return app

@pytest.fixture()
def client(app):
    return app.test_client()