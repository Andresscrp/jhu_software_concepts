"""
app.py

Flask web application for displaying GradCafe SQL analysis.

Features:
- Displays results of Module 3 analytical queries.
- Allows reloading data from Module 2 and Module 3 pipeline.
- Prevents concurrent data pulls using a lock file.
- Connects directly to PostgreSQL using fixed credentials.
"""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Any

import os
from flask import Flask, redirect, render_template_string, url_for, jsonify
import psycopg


# --------------------------------------------------
# Project Paths and Constants
# --------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
LOCK_FILE = APP_DIR / "pull.lock"
DEFAULT_LOCK_FILE = LOCK_FILE

FALL_2026 = "Fall 2026"
MIN_SAMPLE_Q10 = 25


# --------------------------------------------------
# HTML Template
# --------------------------------------------------

PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Andres' GradCafe Data Analysis</title>

  <style>
    body { font-family: Times New Roman, sans-serif; margin: 24px; }

    .topbar {
      display:flex;
      align-items:center;
      justify-content:space-between;
    }

    .btn {
      padding: 10px 14px;
      border: 1px solid #111;
      background: #111;
      color: #fff;
      cursor:pointer;
    }

    .btn.secondary {
      background: #fff;
      color:#111;
    }

    .btn[disabled] {
      opacity: .5;
      cursor:not-allowed;
    }

    .note {
      margin: 10px 0 18px;
      color: #333;
    }

    table {
      border-collapse: collapse;
      width: 100%;
      margin-top: 10px;
    }

    th, td {
      border: 1px solid #ccc;
      padding: 8px;
      text-align:left;
    }

    th {
      background: #f2f2f2;
    }

    .card {
      border:1px solid #ddd;
      padding: 14px;
      margin: 14px 0;
      border-radius: 8px;
    }

    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    .btn-desc {
      margin-top: 6px;
      font-size: 14px;
      color: #333;
    }

    .update-form {
      text-align: center;
      margin-top: 10px;
    }

  </style>
</head>

<body>

  <div class="topbar">
    <h2>Andres' GradCafe Data Analysis</h2>

    <form method="post" action="{{ url_for('update_analysis') }}"> 
      <button class="update-form"
            type="submit"
            data-testid="update-analysis-btn"
            {% if pulling %}disabled{% endif %}>
        Update Analysis
      </button>

      <div class="btn-desc">
        Re-runs the SQL queries and refreshes the dashboard using the data already in PostgreSQL.        
      </div>
    </form>


  </div>


  <div class="note">
    <form method="post" action="{{ url_for('pull_data') }}">

      <button class="btn"
              type="submit"
              data-testid="pull-data-btn"
              {% if pulling %}disabled{% endif %}>
        Pull Data
      </button>

      <span style="margin-left:10px;">

        Pull Data fetches the latest GradCafe results, processes them, and updates the analysis database.

        {% if pulling %}
          <b>Pull currently running.</b>
        {% endif %}

      </span>

    </form>
  </div>


  {% for block in blocks %}

    <div class="card">

      <div><b>{{ block.title }}</b></div>
      <div><b>Answer:</b></div>

      <div class="mono" style="margin-top:8px;">

        {% if block.rows and block.headers %}

          <table>

            <thead>
              <tr>
                {% for h in block.headers %}
                  <th>{{ h }}</th>
                {% endfor %}
              </tr>
            </thead>

            <tbody>

              {% for r in block.rows %}
                <tr>

                  {% for cell in r %}
                    <td>{{ cell }}</td>
                  {% endfor %}

                </tr>
              {% endfor %}

            </tbody>

          </table>

        {% else %}

          <div>No results.</div>

        {% endif %}

      </div>

    </div>

  {% endfor %}

</body>
</html>
"""


# --------------------------------------------------
# Lock Management
# --------------------------------------------------

def lock_exists() -> bool:
    """
    Check whether a data pull operation is currently running.

    Returns:
        True if the lock file exists.
    """
    return LOCK_FILE.exists()


def create_lock() -> None:
    """
    Create a lock file to indicate an active data pull.
    """
    LOCK_FILE.write_text("running", encoding="utf-8")

def remove_lock() -> None:
    """
    Remove the lock file when a data pull finishes.
    """
    if LOCK_FILE.exists(): 
        LOCK_FILE.unlink()


# --------------------------------------------------
# Database Connection
# --------------------------------------------------

def get_conn() -> psycopg.Connection:
    """
    Create and return a PostgreSQL connection using DATABASE_URL.

    For tests, allow overriding the connection string via Flask config:
    app.config["DATABASE_URL"].
    """

    # If tests created the app and injected a DB URL, use it.
    try:
        from flask import current_app
        cfg_url = current_app.config.get("DATABASE_URL")  # type: ignore[attr-defined]
    except Exception:
        cfg_url = None

    db_url = cfg_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return psycopg.connect(db_url)


# --------------------------------------------------
# Query Helper
# --------------------------------------------------

def fetch_one(
    sql: str,
    params: dict[str, Any] | None = None
) -> tuple[list[str], list[tuple]]:
    """
    Execute a SQL query and return column headers and rows.

    Args:
        sql: SQL query string.
        params: Optional parameter dictionary.

    Returns:
        Tuple of (column names, query results).
    """

    with get_conn() as conn:

        with conn.cursor() as cur:

            cur.execute(sql, params or {})

            rows = cur.fetchall()

            headers = (
                [d.name for d in cur.description]
                if cur.description else []
            )

    return headers, rows


# --------------------------------------------------
# Analysis Builder
# --------------------------------------------------

def build_blocks() -> list[dict[str, Any]]:
    """
    Execute all rubric and extra credit queries.

    Returns:
        List of result blocks for rendering.
    """

    blocks: list[dict[str, Any]] = []


    # ---------------- Q1 ----------------

    h, r = fetch_one(
        "SELECT COUNT(*) AS fall_2026_entries "
        "FROM applicants WHERE term = %(t)s;",
        {"t": FALL_2026},
    )

    blocks.append({
        "title": "Q1) How many entries do you have in your database that have applied for Fall 2026?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q2 ----------------

    h, r = fetch_one("""
        SELECT
          ROUND(
            100.0 * SUM(
              CASE
                WHEN us_or_international
                     NOT IN ('American','Other')
                THEN 1 ELSE 0
              END
            )::numeric
            / NULLIF(COUNT(*),0),
            2
          ) AS pct_international
        FROM applicants
        WHERE us_or_international IS NOT NULL;
    """)

    blocks.append({
        "title": "Q2) What percentage of entries are from international students?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q3 ----------------

    h, r = fetch_one("""
        SELECT
          ROUND(AVG(gpa)::numeric,2)    AS avg_gpa,
          ROUND(AVG(gre)::numeric,2)    AS avg_gre,
          ROUND(AVG(gre_v)::numeric,2)  AS avg_gre_v,
          ROUND(AVG(gre_aw)::numeric,2) AS avg_gre_aw
        FROM applicants
        WHERE gpa>0 AND gre>0
          AND gre_v>0 AND gre_aw>0;
    """)

    blocks.append({
        "title": "Q3) What is the average GPA, GRE, GRE V, and GRE AW of applicants who provide these metrics?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q4 ----------------

    h, r = fetch_one("""
        SELECT ROUND(AVG(gpa)::numeric,2)
        FROM applicants
        WHERE term=%(t)s
          AND us_or_international='American'
          AND gpa>0;
    """, {"t": FALL_2026})

    blocks.append({
        "title": "Q4) What is the average GPA of American students in Fall 2026?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q5 ----------------

    h, r = fetch_one("""
        SELECT
          ROUND(
            100.0 * SUM(
              CASE WHEN status='Accepted'
              THEN 1 ELSE 0 END
            )::numeric
            / NULLIF(COUNT(*),0),
            2
          )
        FROM applicants
        WHERE term=%(t)s;
    """, {"t": FALL_2026})

    blocks.append({
        "title": "Q5) What percent of entries for Fall 2026 are Acceptances?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q6 ----------------

    h, r = fetch_one("""
        SELECT ROUND(AVG(gpa)::numeric,2)
        FROM applicants
        WHERE term=%(t)s
          AND status='Accepted'
          AND gpa>0;
    """, {"t": FALL_2026})

    blocks.append({
        "title": "Q6) What is the average GPA of applicants who applied for Fall 2026 and were accepted?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q7 ----------------

    h, r = fetch_one("""
        SELECT COUNT(*)
        FROM applicants
        WHERE program ILIKE '%%johns hopkins%%'
          AND program ILIKE '%%computer science%%'
          AND (
            degree ILIKE 'm%%'
            OR degree ILIKE '%%master%%'
            OR degree ILIKE '%%ms%%'
          );
    """)

    blocks.append({
        "title": "Q7) How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q8 ----------------

    h, r = fetch_one("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term=%(t)s
          AND status='Accepted'
          AND degree ILIKE 'phd%%'
          AND program ILIKE '%%computer science%%'
          AND (
            program ILIKE '%%georgetown%%'
            OR program ILIKE '%%mit%%'
            OR program ILIKE '%%stanford%%'
            OR program ILIKE '%%carnegie%%'
          );
    """, {"t": FALL_2026})

    blocks.append({
        "title": "Q8) How many entries from 2026 are acceptances from applicants who applied to Georgetown University, MIT, Stanford University, or Carnegie Mellon University for a PhD in Computer Science?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q9 ----------------

    h, r = fetch_one("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term=%(t)s
          AND status='Accepted'
          AND degree ILIKE 'phd%%'
          AND llm_generated_program
              ILIKE '%%computer science%%'
          AND (
            llm_generated_university ILIKE '%%georgetown%%'
            OR llm_generated_university ILIKE '%%mit%%'
            OR llm_generated_university ILIKE '%%stanford%%'
            OR llm_generated_university ILIKE '%%carnegie%%'
          );
    """, {"t": FALL_2026})

    blocks.append({
        "title": "Q9) Do your numbers for question 8 change if you use LLM-generated fields (rather than your downloaded fields)?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q10 ----------------

    h, r = fetch_one("""
        SELECT
          program,
          COUNT(*) AS total,
          SUM(CASE WHEN status='Accepted'
              THEN 1 ELSE 0 END) AS accepted,
          ROUND(
            SUM(CASE WHEN status='Accepted'
                THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*),0) * 100,
            2
          ) AS rate
        FROM applicants
        WHERE term=%(t)s
        GROUP BY program
        HAVING COUNT(*) >= %(n)s
        ORDER BY rate DESC
        LIMIT 10;
    """, {"t": FALL_2026, "n": MIN_SAMPLE_Q10})

    blocks.append({
        "title": "Q10) What are the top 10 programs with the highest acceptance rate?",
        "headers": h,
        "rows": r
    })


    # ---------------- Q11 ----------------

    h, r = fetch_one("""
        SELECT
          status,
          ROUND(AVG(gre)::numeric,2)
        FROM applicants
        WHERE term=%(t)s
          AND gre>0
        GROUP BY status
        ORDER BY 2 DESC;
    """, {"t": FALL_2026})

    blocks.append({
        "title": "Q11) What is the average GRE of each status category?",
        "headers": h,
        "rows": r
    })


    return blocks


# --------------------------------------------------
# Data Pipeline
# --------------------------------------------------

def run_pull_pipeline() -> None:
    """
    Execute scraping, cleaning, and loading pipeline.

    Prevents concurrent execution using a lock file.
    """
    try:
        create_lock()

        scrape = ROOT_DIR / "module_3" / "scrape.py"
        clean = ROOT_DIR / "module_3" / "clean.py"

        if scrape.exists():
            subprocess.run(["python", str(scrape)], check=True)

        if clean.exists():
            subprocess.run(["python", str(clean)], check=True)

        subprocess.run(["python", str(APP_DIR / "load_data.py")], check=True)

    finally:
        remove_lock()


# --------------------------------------------------
# Flask App
# --------------------------------------------------

def create_app(
    *,
    build_blocks_fn=build_blocks,
    lock_exists_fn=lock_exists,
    run_pull_fn=run_pull_pipeline,
) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        build_blocks_fn: Function that returns the analysis blocks for rendering.
        lock_exists_fn: Function that reports whether a pull is in progress.
        run_pull_fn: Function that performs the pull/load pipeline.

    Returns:
        Configured Flask app instance for running or testing.
    """
    app = Flask(__name__)

    @app.get("/")
    def index():
        """Redirect root to the analysis page for a stable testing URL."""
        return redirect(url_for("analysis"))

    @app.get("/analysis")
    def analysis():
        """Render main analysis page."""
        pulling = lock_exists_fn()
        blocks = build_blocks_fn()
        return render_template_string(PAGE, pulling=pulling, blocks=blocks)

    @app.post("/pull-data")
    def pull_data():
        """Trigger background data pull."""
        if lock_exists_fn():
            return jsonify({"busy": True}), 409

        t = threading.Thread(target=run_pull_fn, daemon=True)
        t.start()
        return jsonify({"ok": True}), 202

    @app.post("/update-analysis")
    def update_analysis():
        """Refresh analysis results."""
        if lock_exists_fn():
            return jsonify({"busy": True}), 409
        return jsonify({"ok": True}), 200

    return app


app = create_app()

