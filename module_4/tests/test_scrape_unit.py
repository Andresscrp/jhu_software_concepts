"""
test_scrape_unit.py

Unit tests for src/scrape.py that do not touch the network.

Covers:
- extract_result_urls_from_survey: link discovery + uniqueness
"""

import pytest

import src.scrape as scrape


@pytest.mark.analysis
def test_extract_result_urls_from_survey_unique_and_full_urls():
    """extract_result_urls_from_survey should return unique full /result/<id> URLs."""
    html = """
    <html><body>
      <a href="/result/123">A</a>
      <a href="/result/123">dup</a>
      <a href="/result/999">B</a>
      <a href="/survey/">ignore</a>
      <a href="/result/notanid">ignore</a>
    </body></html>
    """
    urls = scrape.extract_result_urls_from_survey(html)
    assert urls == [
        "https://www.thegradcafe.com/result/123",
        "https://www.thegradcafe.com/result/999",
    ]
