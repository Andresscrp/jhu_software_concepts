"""
test_analysis_format.py

Tests for formatting of numeric output and presence of answer labels
on the analysis page.
"""

import re

import pytest
from bs4 import BeautifulSoup

from src import app as appmod


@pytest.mark.analysis
def test_page_includes_answer_labels_and_two_decimal_numbers():
    """
    Ensure analysis page includes 'Answer:' labels and at least one
    two-decimal formatted numeric value.
    """

    def fake_blocks():
        return [
            {
                "title": "Q2) Percent",
                "headers": ["pct_international"],
                "rows": [(39.28,)],
            },
            {
                "title": "Q5) Percent",
                "headers": ["pct_accepted"],
                "rows": [(12.00,)],
            },
        ]

    app = appmod.create_app(
        build_blocks_fn=fake_blocks,
        lock_exists_fn=lambda: False,
    )
    app.config.update(TESTING=True)
    client = app.test_client()

    resp = client.get("/analysis")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    assert "Answer:" in page_text
    assert re.search(r"\b\d+\.\d{2}\b", page_text) is not None
