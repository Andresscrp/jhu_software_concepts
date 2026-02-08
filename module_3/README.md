# Module 3 — PostgreSQL Analysis & Flask Web App

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** 605.256 Modern Software Concepts in Python  
**Module:** Module 3 — Assignment: SQL Analysis & Web Application

---

## Sources
- Course lecture materials
- PostgreSQL documentation
- Flask documentation

---

## Overview

This project loads cleaned GradCafe admissions data into a PostgreSQL database, runs analytical SQL queries to answer assignment questions, and displays the results on a Flask web dashboard.

The application allows users to refresh analysis results and re-run the data pipeline while preventing concurrent executions.

---

## Repository Structure (Required Deliverables)

- `module_3/app.py` — Flask web application for displaying SQL analysis
- `module_3/load_data.py` — Loads cleaned JSON data into PostgreSQL
- `module_3/query_data.py` — Runs SQL queries for assignment questions
- `module_3/requirements.txt` — Project dependencies
- `module_3/README.md` — Project documentation
- `module_3\llm_extend_applicant_data.json` - LLM extended data for queries
- `module_3/scrape.py` – pulls raw applicant data from GradCafe
- `module_3/clean.py` – loads raw data, cleans/structures it, saves JSON outputs

---

## Approach

### Step 1 — Database Setup
- Created a PostgreSQL database (`module_3db`)
- Defined schema for applicant data
- Configured database credentials in Python scripts

### Step 2 — Data Loading
- Used `load_data.py` to read JSON data
- Inserted records into the `applicants` table
- Validated successful data import

### Step 3 — SQL Analysis
- Implemented assignment queries in `query_data.py`
- Used parameterized SQL for safety and flexibility
- Generated statistics for GPA, GRE, acceptance rates, and institutions

### Step 4 — LLM Field Comparison
- Compared downloaded fields with LLM-generated program and university fields
- Evaluated differences in query results for Question 9

### Step 5 — Flask Web Interface
- Built a single-page Flask dashboard in `app.py`
- Displayed query results in formatted tables
- Added buttons for updating analysis and pulling new data
- Used a lock file to prevent concurrent pipeline execution

---

## How to Run

### Step 1 — Install Dependencies

From the project root:

```bash
pip install -r module_3/requirements.txt
