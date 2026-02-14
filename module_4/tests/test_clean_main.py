"""
test_clean_main.py

Covers src/clean.py:
- main() file read/clean/write body
- module entrypoint: if __name__ == "__main__": main()
"""

import json
import runpy
from pathlib import Path

import src.clean as clean


def test_clean_runs_main_and_writes_output(tmp_path, monkeypatch):
    """
    Covers clean.py main() body (the file read/clean/write lines).
    """
    # Run in a temporary working directory so we don't touch repo files
    monkeypatch.chdir(tmp_path)

    # These are the filenames clean.py uses (they are relative paths)
    input_path = Path("applicant_data.json")
    output_path = Path("cleaned_applicant_data.json")

    # Write a tiny input JSON file
    sample = [
        {
            "program": "Test U - CS",
            "comments": None,
            "date_added": "January 31, 2026",
            "url": "https://example.com/x",
            "status": "Accepted",
            "term": "Fall 2026",
            "us_or_international": "American",
            "gpa": "3.90",
        }
    ]
    input_path.write_text(json.dumps(sample), encoding="utf-8")

    # Remove output if it exists
    if output_path.exists():
        output_path.unlink()

    # Call main() directly
    clean.main()

    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 1


def test_clean_module_entrypoint_runs(tmp_path, monkeypatch):
    """
    Covers the `if __name__ == "__main__": main()` line by running the module as __main__.
    """
    # Run in a temporary working directory so clean.py finds applicant_data.json
    monkeypatch.chdir(tmp_path)

    # Create the file that clean.py expects in the current working directory
    Path("applicant_data.json").write_text(json.dumps([]), encoding="utf-8")

    # Run the module as __main__
    runpy.run_module("src.clean", run_name="__main__")

    # And verify it produced the expected output file
    assert Path("cleaned_applicant_data.json").exists()
