"""
load_data.py

Loads GradCafe data into PostgreSQL.
"""

from __future__ import annotations

import json
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
INPUT_JSON = Path("../module_3/llm_extend_applicant_data.json")

# --------------------
# HELPERS
# --------------------

def clean_text(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).replace("\x00", "").strip()
    return s if s else None


def to_float(x: Any) -> Optional[float]:
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
    """Convert '30/01/2026' -> date (your old dataset)"""
    s = clean_text(s)
    if not s:
        return None
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_date_monthname(s: Any):
    """Convert 'January 31, 2026' -> date (professor dataset)"""
    s = clean_text(s)
    if not s:
        return None
    try:
        return datetime.strptime(s, "%B %d, %Y").date()
    except ValueError:
        return None


def derive_term_from_date(d):
    if not d:
        return None
    return f"Fall {d.year}"


def join_program(institution: Any, program: Any) -> Optional[str]:
    """
    Professor LLM file already has combined "program".
    """
    inst = clean_text(institution)
    prog = clean_text(program)
    if inst and prog:
        return f"{inst} - {prog}"
    return inst or prog


def read_records(path: Path) -> List[Dict[str, Any]]:
    """
    Reads either:
    - JSON list
    - JSONL (one json object per line)
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
    Map BOTH dataset styles into the DB columns created.
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

def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(INPUT_JSON)

    records = read_records(INPUT_JSON)
    print(f"Loaded {len(records)} records from {INPUT_JSON}")

    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    INSERT_SQL = """
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
    );
    """

    inserted = 0

    with conn:
        with conn.cursor() as cur:
            for row in records:
                data = normalize_row(row)
                cur.execute(INSERT_SQL, data)
                inserted += 1

    conn.close()
    print(f"Inserted {inserted} rows.")


if __name__ == "__main__":
    main()
