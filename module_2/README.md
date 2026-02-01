**Name:** Andres Sanchez-Castellanos
**JHED ID:** asanch69  
**Course:** 605.256 Modern Software Concepts in Python  
**Module:** Module 2 – Assignment: Web Scraping

---
### SOURCES: https://realpython.com/python-web-scraping-practical-introduction/, https://realpython.com/beautiful-soup-web-scraper-python/, ChatGPT

## Overview

This project scrapes GradCafe results pages, parses applicant admissions data, and saves it as structured JSON for later analysis. It also produces a cleaned dataset using a locally hosted tiny LLM (provided starter package under `module_2/llm_hosting/`) to standardize program and university names.

---

## Repository Structure (Required Deliverables)

- `module_2/scrape.py` – pulls raw applicant data from GradCafe
- `module_2/clean.py` – loads raw data, cleans/structures it, saves JSON outputs
- `module_2/applicant_data.json` – raw scraped output (30,000+ entries target)
- `module_2/llm_extend_applicant_data.json` – cleaned output with standardized fields
- `module_2/robots.txt` – robots rules saved for reference
- `module_2/screenshot.jpg` – evidence robots.txt was checked
- `module_2/requirements.txt` – reproducible environment for module_2
- `module_2/llm_hosting/` – instructor-provided LLM hosting subpackage + my run notes

---

## Approach

### Step 1 — Robots.txt compliance
- Verified that GradCafe’s `robots.txt` permits scraping the needed endpoints.
- Saved `robots.txt` and included `screenshot.jpg` evidence.

### Step 2 — Scraping (Part I)
- Uses `urllib` for URL management and requesting pages.
- Uses BeautifulSoup + string methods / regex to extract applicant fields.
- Extracted fields include:
  - Program name (raw)
  - University (if available / parsed)
  - Comments (if available)
  - Date added
  - Result URL
  - Applicant status + acceptance/rejection date (when available)
  - Term (semester + year when available)
  - US/International (when available)
  - GRE / GPA / Degree fields when available

### Step 3 — Cleaning (Part II)
- Converts scraped results into consistent dictionaries.
- Ensures missing data is kept consistent (e.g., `None` or empty string).
- Strips/avoids remnant HTML.
- Writes clean JSON outputs for downstream analysis.

### Step 4 — LLM standardization (Part III)
- Runs the provided local LLM hosting tool in `module_2/llm_hosting/` to standardize:
  - `llm-generated-program`
  - `llm-generated-university`
- Kept the original `program` field unchanged for traceability.

---

## How to Run

### Part I: Scrape
From repo root:

```bash
python module_2/scrape.py

### Part II: Clean and save outputs
python module_2/clean.py

### Part III: LLM hosting standardizer
cd module_2/llm_hosting
pip install -r requirements.txt
python app.py --file sample_data.json --out sample_output.json

Format:

@'
{"rows":[
  {"program":"Information Studies, McG"},
  {"program":"Mathematics, University Of British Columbia"},
  {"program":"Computer Science, uoft"}
]}
'@ | Out-File -Encoding utf8 sample_input.json


