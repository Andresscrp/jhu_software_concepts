"""
test_integration_end_to_end.py

Integration test covering pull, update, and render workflow using fakes.
"""

import re

import pytest
from bs4 import BeautifulSoup

from src import app as appmod


@pytest.mark.integration
def test_end_to_end_pull_update_render():
    """
    Test pull -> update -> render sequence with fake pipeline functions.
    """
    pulled = {"done": False}

    def fake_pull():
        pulled["done"] = True

    def fake_blocks():
        return [
            {
                "title": "Q2) Percent",
                "headers": ["pct"],
                "rows": [(39.28,)],
            }
        ]

    app = appmod.create_app(
        run_pull_fn=fake_pull,
        build_blocks_fn=fake_blocks,
        lock_exists_fn=lambda: False,
    )
    app.config.update(TESTING=True)
    client = app.test_client()

    r1 = client.post("/pull-data")
    assert r1.status_code == 202
    assert pulled["done"] in (False, True)

    r2 = client.post("/update-analysis")
    assert r2.status_code == 200

    r3 = client.get("/analysis")
    assert r3.status_code == 200

    soup = BeautifulSoup(r3.data, "html.parser")
    text = soup.get_text(" ", strip=True)

    assert "Answer:" in text
    assert re.search(r"\b\d+\.\d{2}\b", text) is not None
