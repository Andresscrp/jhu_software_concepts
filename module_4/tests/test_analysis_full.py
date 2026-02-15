import pytest
from src import app as appmod



def fake_fetch_one(sql, params=None):
    """Return deterministic fake SQL results."""
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
