"""
load_data.py

Loads GradCafe data into PostgreSQL.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg


# --------------------
# DATABASE CONFIG
# --------------------

DB_NAME = "module_3db"
DB_USER = "postgres"
DB_PASSWORD = "Aasc060602"
DB_HOST = "localhost"
DB_PORT = 5432


# --------------------
# INPUT FILE
# --------------------
INPUT_JSON = Path("../module_4/src/llm_extend_applicant_data.json")

# --------------------
# HELPERS
# --------------------


def clean_text(x: Any) -> Optional[str]:
    """
    Convert a value to a cleaned string for database insertion.

    Returns None for missing/blank values and strips null bytes and whitespace.
    """
    if x is None:
        return None
    s = str(x).replace("\x00", "").strip()
    return s if s else None


def to_float(x: Any) -> Optional[float]:
    """
    Convert a value to float when possible.

    Supports numeric types directly and extracts the first numeric token from strings
    (e.g., "GPA 3.89" -> 3.89). Returns None when missing or invalid.
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)

    s = clean_text(x)
    if not s:
        return None

    # Handles things like "GPA 3.89" or "3.89"
    m = re.search(r"(-?\d+(?:\.\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def parse_date_ddmmyyyy(s: Any):
    """Convert '30/01/2026' -> date (your old dataset)."""
    s = clean_text(s)
    if not s:
        return None
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_date_monthname(s: Any):
    """Convert 'January 31, 2026' -> date (professor dataset)."""
    s = clean_text(s)
    if not s:
        return None
    try:
        return datetime.strptime(s, "%B %d, %Y").date()
    except ValueError:
        return None


def derive_term_from_date(d):
    """
    Derive an application term label from a date.

    Example: a date in 2026 becomes "Fall 2026". Returns None if the date is missing.
    """
    if not d:
        return None
    return f"Fall {d.year}"


def join_program(institution: Any, program: Any) -> Optional[str]:
    """
    Combine institution and program when both are present.

    Professor LLM file already has combined "program", so this is mainly used when
    loading the older dataset format.
    """
    inst = clean_text(institution)
    prog = clean_text(program)
    if inst and prog:
        return f"{inst} - {prog}"
    return inst or prog


def read_records(path: Path) -> List[Dict[str, Any]]:
    """
    Read records from a JSON list file or a JSONL file.

    Returns a list of dictionaries, one per applicant record.
    """
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        raise ValueError("Top-level JSON is not a list (this file might be JSONL).")
    except json.JSONDecodeError:
        # JSONL fallback
        records: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map either dataset style into the DB columns used by the applicants table.

    This supports both the professor-provided LLM dataset and the earlier scraped
    dataset format by normalizing keys and data types.
    """
    # ----- term -----
    term = clean_text(row.get("semester_year_start"))
    if not term:
        # Your file: derive from notification_date dd/mm/yyyy
        d_notification = parse_date_ddmmyyyy(row.get("notification_date"))
        term = derive_term_from_date(d_notification)

    # ----- date_added -----
    date_added = parse_date_monthname(row.get("date_added"))
    if not date_added:
        # Your: notification_date dd/mm/yyyy
        date_added = parse_date_ddmmyyyy(row.get("notification_date"))

    # ----- status -----
    status = clean_text(row.get("applicant_status"))
    if not status:
        status = clean_text(row.get("decision"))

    # ----- citizenship / country -----
    citizenship = clean_text(row.get("citizenship"))
    if not citizenship:
        citizenship = clean_text(row.get("country_of_origin"))

    # ----- degree -----
    degree = clean_text(row.get("masters_or_phd"))
    if not degree:
        degree = clean_text(row.get("degree"))

    # ----- program -----
    program = clean_text(row.get("program"))
    # Your file: combine institution + program (if needed)
    if not program:
        program = join_program(row.get("institution"), row.get("program"))

    # ----- comments -----
    comments = clean_text(row.get("comments"))
    if comments is None:
        comments = clean_text(row.get("notes"))

    # ----- llm fields -----
    llm_prog = clean_text(row.get("llm-generated-program"))
    if llm_prog is None:
        llm_prog = clean_text(row.get("llm_generated_program"))

    llm_uni = clean_text(row.get("llm-generated-university"))
    if llm_uni is None:
        llm_uni = clean_text(row.get("llm_generated_university"))

    return {
        "program": program,
        "comments": comments,
        "date_added": date_added,
        "url": clean_text(row.get("url")),
        "status": status,
        "term": term,
        "country": citizenship,
        "gpa": to_float(row.get("gpa") if "gpa" in row else row.get("undergrad_gpa")),
        "gre": to_float(row.get("gre") if "gre" in row else row.get("gre_general")),
        "gre_v": to_float(row.get("gre_v") if "gre_v" in row else row.get("gre_verbal")),
        "gre_aw": to_float(row.get("gre_aw")),
        "degree": degree,
        "llm_program": llm_prog,
        "llm_university": llm_uni,
    }


# --------------------
# MAIN
# --------------------


def main() -> None:
    """
    Load the input JSON records and insert normalized rows into PostgreSQL.

    The database connection is read from the DATABASE_URL environment variable.
    """
    if not INPUT_JSON.exists():
        raise FileNotFoundError(INPUT_JSON)

    records = read_records(INPUT_JSON)
    print(f"Loaded {len(records)} records from {INPUT_JSON}")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    insert_sql = """
    INSERT INTO applicants (
        program,
        comments,
        date_added,
        url,
        status,
        term,
        us_or_international,
        gpa,
        gre,
        gre_v,
        gre_aw,
        degree,
        llm_generated_program,
        llm_generated_university
    )
    VALUES (
        %(program)s,
        %(comments)s,
        %(date_added)s,
        %(url)s,
        %(status)s,
        %(term)s,
        %(country)s,
        %(gpa)s,
        %(gre)s,
        %(gre_v)s,
        %(gre_aw)s,
        %(degree)s,
        %(llm_program)s,
        %(llm_university)s
    )
    ON CONFLICT (url) DO NOTHING;
    """

    inserted = 0

    # Open ONE connection context and do everything inside it
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Ensure uniqueness constraint exists (safe to run repeatedly)
            cur.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'applicants_url_unique'
                    ) THEN
                        ALTER TABLE applicants
                        ADD CONSTRAINT applicants_url_unique UNIQUE (url);
                    END IF;
                END
                $$;
                """
            )

            # Insert all rows
            for row in records:
                data = normalize_row(row)
                cur.execute(insert_sql, data)

                # Count "attempted inserts" (not true inserted rows)
                inserted += 1

        # conn commits automatically on clean exit of the with-block

    print(f"Processed {inserted} rows (attempted inserts).")
    print(f"Inserted {inserted} rows.")


if __name__ == "__main__":
    main()
