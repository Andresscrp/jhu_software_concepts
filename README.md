# Module 4 — Testing & Documentation (Pytest + Sphinx)

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** 605.256 Modern Software Concepts in Python  
**Module:** Module 4 — Assignment: Testing and Documentation

---

## Sources

- Course lecture materials
- Pytest documentation
- pytest-cov documentation
- Flask documentation
- PostgreSQL documentation
- Sphinx documentation
- ChatGPT
- Professor-provided LLM-extended dataset (`llm_extend_applicant_data.json`)

---

## Overview

This project extends the GradCafe analytics service from Module 3 by adding:

- A complete Pytest suite covering the Flask UI, button behavior, formatting rules, database inserts, and end-to-end flows
- 100% test coverage enforced via `pytest-cov` (`--cov-fail-under=100`)
- Test organization using required Pytest markers
- Sphinx documentation
- Continuous Integration using GitHub Actions

The Flask app serves an **Analysis** page and exposes two endpoints:

- **POST `/pull-data`** — triggers a background ETL pull/load
- **POST `/update-analysis`** — refreshes analysis (busy-gated if a pull is running)

Busy-state behavior is enforced using a lock file.

---

## Repository Structure

src/
app.py
scrape.py
clean.py
load_data.py
run.py

tests/
test_flask_page.py
test_buttons.py
test_analysis_format.py
test_db_insert.py
test_integration_end_to_end.py
test_run_py.py
test_clean_main.py

docs/
Sphinx documentation

.github/workflows/
tests.yml

coverage_summary.txt
actions_success.png
pytest.ini
requirements.txt
README.md


---

## Environment Variables

This project uses `DATABASE_URL` for PostgreSQL connectivity.

Example (PowerShell):

```powershell
$env:DATABASE_URL = "postgresql://postgres:<PASSWORD>@localhost:5432/module_3db"

---

## Running the App

Set the base URL:
$env:DATABASE_URL="postgresql://postgres:<PASSWORD>@localhost:5432/module_3db"

Run the Flask app:

py -m src.run

Open in browser:

http://127.0.0.1:5000/analysis

