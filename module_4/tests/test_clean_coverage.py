import pytest
import src.clean as cleanmod


@pytest.mark.analysis
def test_clean_covers_missing_branches():
    # TODO: adjust this dict to trigger the uncovered lines 140-149 and 152
    sample = {
        # put keys here that your clean_record() expects
    }

    # If your file has clean_record():
    if hasattr(cleanmod, "clean_record"):
        out = cleanmod.clean_record(sample)
        assert out is not None

    # If your file has helper functions used in those lines, call them too:
    # e.g. clean_text / to_float / parse_date etc.
