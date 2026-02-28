"""
test_analysis_full.py

Tests that the full analysis pipeline executes without requiring a live database.
"""

import pytest

from src import app as appmod


def fake_fetch_one(_sql, _params=None):
    """
    Return deterministic fake SQL results.

    Arguments are unused and replaced with dummy values for testing.
    """
    return ["col"], [(1,)]


@pytest.mark.analysis
def test_build_blocks_executes_all_queries(monkeypatch):
    """
    Ensure build_blocks() runs all SQL blocks without hitting Postgres.
    """
    monkeypatch.setattr(appmod, "fetch_one", fake_fetch_one)

    blocks = appmod.build_blocks()

    assert isinstance(blocks, list)
    assert len(blocks) >= 10
