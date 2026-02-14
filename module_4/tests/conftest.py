import pytest

import src.app as appmod


# If the user/CI didn't set DATABASE_URL, give tests a default.
# (CI Postgres service usually uses postgres/postgres on db "postgres")

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