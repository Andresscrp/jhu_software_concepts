# Module 5 — Software Assurance + Secure SQL (SQLi Defense)

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** 605.256 Modern Software Concepts in Python  
**Module:** Module 5 — Software Assurance + Secure SQL

---

## Sources

- Course lecture materials  
- Flask documentation  
- Psycopg documentation  
- PostgreSQL documentation  
- Pytest / pytest-cov documentation  
- Pylint documentation  
- PyDeps documentation  
- Graphviz documentation  
- Snyk documentation  
- ChatGPT  
- Professor-provided LLM-extended dataset (`llm_extend_applicant_data.json`)

---

## Overview

This project extends the GradCafe analytics system by applying software assurance and security practices.

It includes:

- 10/10 Pylint static analysis  
- SQL injection defenses using parameterized queries  
- Mandatory LIMIT enforcement  
- Least-privilege PostgreSQL user configuration  
- Dependency graph generation with pydeps + Graphviz  
- Reproducible virtual environments (pip + uv)  
- Dependency vulnerability scanning with Snyk  
- Continuous Integration enforcement with GitHub Actions  
- 100% Pytest coverage  

The Flask application serves an Analysis Dashboard and supports controlled ETL execution.

Endpoints:

- POST `/pull-data` — runs ETL pipeline  
- POST `/update-analysis` — refreshes analysis results  
- GET `/analysis` — main dashboard  

Concurrency is managed using a lock file.

---

## Repository Structure

```
module_5/

src/
  app.py
  clean.py
  load_data.py
  run.py
  sql_utils.py

tests/
  test_app_coverage.py
  test_db_insert.py
  test_sql_utils_cover.py

docs/
  Sphinx documentation

.github/workflows/
  ci.yml

dependency.svg
pytest.ini
requirements.txt
setup.py
README.md
.env.example
```

---

## Virtual Environment Setup

### Create Virtual Environment

```powershell
python -m venv .venv
```

### Activate Virtual Environment (Every Time)

```powershell
.venv\Scripts\Activate.ps1
```

You should see:

```
(.venv)
```

in your terminal.

### Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## Environment Variables

This project uses environment variables for database credentials.

### Required

- DATABASE_URL  
  OR  
- DB_HOST  
- DB_PORT  
- DB_NAME  
- DB_USER  
- DB_PASSWORD  

### Example (.env.example)

```
DATABASE_URL=postgresql://app_user:password@localhost:5432/module_3db
```

### Load .env (PowerShell)

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match "=") {
    $name, $value = $_ -split "=", 2
    Set-Item env:$name $value
  }
}
```

---

## Running the Application

### Set Database URL

```powershell
$env:DATABASE_URL="postgresql://app_user:<PASSWORD>@localhost:5432/module_3db"
```

### Start Flask

```powershell
python -m src.app
```

### Open Browser

```
http://127.0.0.1:5000/analysis
```

---

## Running Tests (Pytest)

### All Tests

```powershell
python -m pytest -q
```

### With Coverage

```powershell
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=100
```

Required:

```
TOTAL 100%
```

---

## Static Analysis (Pylint)

```powershell
python -m pylint src --fail-under=10
```

Required:

```
10.00/10
```

---

## SQL Injection Defenses

All SQL queries:

- Use parameter binding  
- No f-strings  
- No concatenation  
- LIMIT enforced  
- Normalized queries  
- Safe validation  

Security handled in `sql_utils.py`.

---

## Database Hardening

Least-privilege user:

```sql
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE applicants TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO app_user;
```

No superuser privileges used.

---

## Dependency Graph (pydeps)

### Install

```powershell
pip install pydeps
```

Install Graphviz separately.

Verify:

```powershell
dot -V
```

### Generate

```powershell
pydeps src/app.py --noshow -T svg -o dependency.svg
```

---

## Packaging (setup.py)

Enable editable install:

```powershell
pip install -e .
```

Improves reproducibility and imports.

---

## Fresh Install

### pip

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

### uv

```powershell
pip install uv
uv venv
.venv\Scripts\Activate.ps1
uv pip sync requirements.txt
```

---

## Snyk Scan

### Authenticate

```powershell
snyk auth
```

### Test

```powershell
snyk test
```

### Monitor (Optional)

```powershell
snyk monitor
```

Screenshot saved as `snyk-analysis.png`.

---

## Continuous Integration

CI runs:

1. Pylint  
2. Pytest  
3. pydeps  
4. Snyk  

Workflow:

```
.github/workflows/ci.yml
```

---

## Final Deliverables

Submitted:

- module_5 folder  
- dependency.svg  
- snyk-analysis.png  
- setup.py  
- README.md  
- PDF report  
- CI workflow  
- GitHub repo  

All rubric requirements satisfied.

---

## Notes

This project demonstrates:

- Secure SQL practices  
- Reproducible builds  
- Supply-chain security  
- Automated testing  
- Defensive Python engineering  