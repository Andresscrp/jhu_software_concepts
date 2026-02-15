"""
test_clean_unit.py

Unit tests for src/clean.py helpers and record cleaning.

These tests are pure (no file I/O) and drive coverage for:
- blank_to_none
- to_int / to_float
- normalize_decision
- parse_notification
- clean_record
"""

import pytest
from src import app as appmod
import src.clean as clean


@pytest.mark.analysis
def test_blank_to_none():
    """blank_to_none should convert empty/whitespace strings to None."""
    assert clean.blank_to_none("") is None
    assert clean.blank_to_none("   ") is None
    assert clean.blank_to_none("x") == "x"
    assert clean.blank_to_none(5) == 5


@pytest.mark.analysis
def test_to_int_and_to_float():
    """to_int/to_float should parse numbers and return None on invalid."""
    assert clean.to_int("10") == 10
    assert clean.to_int(" 10 ") == 10
    assert clean.to_int("") is None
    assert clean.to_int("nope") is None

    assert clean.to_float("3.5") == 3.5
    assert clean.to_float(" 3.5 ") == 3.5
    assert clean.to_float("") is None
    assert clean.to_float("bad") is None


@pytest.mark.analysis
def test_normalize_decision():
    """normalize_decision should map common decisions to consistent casing."""
    assert clean.normalize_decision("accepted") == "Accepted"
    assert clean.normalize_decision("Rejected") == "Rejected"
    assert clean.normalize_decision("waitlisted") == "Waitlisted"
    assert clean.normalize_decision("") is None
    # unknown values should pass through stripped
    assert clean.normalize_decision("Deferred") == "Deferred"


@pytest.mark.analysis
def test_parse_notification():
    """parse_notification should extract date and method when present."""
    out = clean.parse_notification("on 30/01/2026 via E-mail")
    assert out["notification_date"] == "30/01/2026"
    assert out["notification_method"] == "E-mail"

    out = clean.parse_notification("on 12/01/2026 via Website")
    assert out["notification_date"] == "12/01/2026"
    assert out["notification_method"] == "Website"

    out = clean.parse_notification("")
    assert out["notification_date"] is None
    assert out["notification_method"] is None


@pytest.mark.analysis
def test_clean_record_smoke():
    """clean_record should return normalized types and parsed notification fields."""
    raw = {
        "url": "u",
        "institution": "X",
        "program": "Y",
        "degree": "MS",
        "country_of_origin": "Canada",
        "decision": "accepted",
        "notification": "on 30/01/2026 via E-mail",
        "undergrad_gpa": "3.91",
        "gre_general": "320",
        "gre_verbal": "160",
        "gre_aw": "4.5",
        "notes": "n",
    }
    cleaned = clean.clean_record(raw)
    assert cleaned["decision"] == "Accepted"
    assert cleaned["notification_date"] == "30/01/2026"
    assert cleaned["notification_method"] == "E-mail"
    assert cleaned["undergrad_gpa"] == 3.91
    assert cleaned["gre_general"] == 320
    assert cleaned["gre_verbal"] == 160
    assert cleaned["gre_aw"] == 4.5
