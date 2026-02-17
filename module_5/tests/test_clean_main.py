"""
test_clean_main.py

Tests for src.clean main() execution and script entry-point behavior.
"""

import json
import runpy

import pytest
from src import clean


@pytest.mark.analysis
def test_clean_main_runs_and_writes_file(tmp_path, monkeypatch):
    """
    Covers clean.main() including file IO.
    """
    input_file = tmp_path / "in.json"
    output_file = tmp_path / "out.json"

    data = [{"program": "CS", "gpa": "3.9", "status": "Accepted"}]
    input_file.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(clean, "INPUT_JSON", str(input_file))
    monkeypatch.setattr(clean, "OUTPUT_JSON", str(output_file))

    clean.main()

    assert output_file.exists()
    result = json.loads(output_file.read_text(encoding="utf-8"))
    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.analysis
def test_clean_module_main_guard_runs(tmp_path, monkeypatch):
    """
    Covers the module-level main guard by executing src.clean as a script.
    """
    monkeypatch.chdir(tmp_path)

    (tmp_path / "applicant_data.json").write_text(
        json.dumps([{"program": "Math"}]),
        encoding="utf-8",
    )

    runpy.run_module("src.clean", run_name="__main__")

    assert (tmp_path / "cleaned_applicant_data.json").exists()
