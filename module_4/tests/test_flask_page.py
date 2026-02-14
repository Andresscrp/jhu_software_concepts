"""
test_flask_page.py

Tests for Flask app creation and analysis page rendering.

These tests verify:
- A testable Flask app is created (factory exists and routes are registered).
- GET /analysis returns HTTP 200.
- The analysis page includes required UI components and text.
"""

import pytest
from bs4 import BeautifulSoup

from src.app import create_app
import src.app as appmod

def fake_blocks():
    """Return deterministic blocks so /analysis renders without touching the database."""
    return [{
        "title": "Q1) Fake",
        "headers": ["col"],
        "rows": [(1,)],
    }]

@pytest.mark.web
def test_app_factory_creates_app_with_routes():
    """
    Ensure create_app() returns a Flask app with the required routes.

    This confirms the application is testable and exposes stable endpoints
    used by the grading rubric.
    """
    app = create_app()

    rules = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/analysis" in rules
    assert "/pull-data" in rules
    assert "/update-analysis" in rules


@pytest.mark.web
def test_get_analysis_page_loads(client):
    """
    Ensure GET /analysis loads successfully and renders required components.
    """
    resp = client.get("/analysis")

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    page_text = soup.get_text(" ", strip=True)

    assert "Analysis" in page_text
    assert "Answer:" in page_text

    pull_btn = soup.find(attrs={"data-testid": "pull-data-btn"})
    update_btn = soup.find(attrs={"data-testid": "update-analysis-btn"})

    assert pull_btn is not None
    assert update_btn is not None

    assert "Pull Data" in pull_btn.get_text(strip=True)
    assert "Update Analysis" in update_btn.get_text(strip=True)
