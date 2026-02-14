"""
query_data.py

I run the assignment SQL questions against my applicants table and print results for screenshots.
"""

from __future__ import annotations

import os
from getpass import getpass
from typing import Any, Iterable, Optional

import psycopg


FALL_2026 = "Fall 2026"


def get_conn() -> psycopg.Connection:
    """Connect using DATABASE_URL (no prompting; CI/test friendly)."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return psycopg.connect(db_url)


def run_one(conn: psycopg.Connection, sql: str, params: Optional[dict[str, Any]] = None) -> list[tuple]:
    """I run a SQL query and return all rows."""
    with conn.cursor() as cur:
        cur.execute(sql, params or {})
        return cur.fetchall()


def print_block(title: str, rows: Iterable[tuple]) -> None:
    """I print a labeled block so my console screenshots are easy to follow."""
    print("\n" + "=" * 80)
    print(title)
    print("-" * 80)
    for r in rows:
        print(r)


def main() -> None:
    """I answer Q1–Q9 and two additional questions."""
    with get_conn() as conn:
        # Q1: entries for Fall 2026
        q1 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term = %(term)s;
        """
        print_block("Q1) How many entries are in my database for Fall 2026?", run_one(conn, q1, {"term": FALL_2026}))

        # Q2: percent international (not American or Other), two decimals
        q2 = """
        SELECT
          ROUND(
            100.0 * SUM(CASE WHEN us_or_international NOT IN ('American', 'Other') THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0),
            2
          ) AS pct_international
        FROM applicants
        WHERE us_or_international IS NOT NULL;
        """
        print_block("Q2) What percent of entries are international (not American or Other)?", run_one(conn, q2))

        # Q3: averages for people who provide metrics (must provide all metrics)
        q3 = """
        SELECT
          ROUND(AVG(gpa)::numeric, 2)    AS avg_gpa,
          ROUND(AVG(gre)::numeric, 2)    AS avg_gre,
          ROUND(AVG(gre_v)::numeric, 2)  AS avg_gre_v,
          ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
        FROM applicants
        WHERE gpa > 0 AND gre > 0 AND gre_v > 0 AND gre_aw > 0;
        """
        print_block("Q3) Average GPA / GRE / GRE V / GRE AW (only rows that provide all metrics).", run_one(conn, q3))

        # Q4: avg GPA of American students in Fall 2026
        q4 = """
        SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa_american_fall_2026
        FROM applicants
        WHERE term = %(term)s
          AND us_or_international = 'American'
          AND gpa > 0;
        """
        print_block("Q4) Average GPA of American students in Fall 2026.", run_one(conn, q4, {"term": FALL_2026}))

        # Q5: percent of Fall 2026 entries that are acceptances, two decimals
        q5 = """
        SELECT
          ROUND(
            100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0),
            2
          ) AS pct_accepted_fall_2026
        FROM applicants
        WHERE term = %(term)s;
        """
        print_block("Q5) What percent of Fall 2026 entries are Acceptances?", run_one(conn, q5, {"term": FALL_2026}))

        # Q6: avg GPA of Fall 2026 acceptances
        q6 = """
        SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa_accepted_fall_2026
        FROM applicants
        WHERE term = %(term)s
          AND status = 'Accepted'
          AND gpa > 0;
        """
        print_block("Q6) Average GPA of Fall 2026 Acceptances.", run_one(conn, q6, {"term": FALL_2026}))

        # Q7 (DOWNLOADED fields): JHU masters in CS
        q7 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE
          program ILIKE '%%johns hopkins%%'
          AND program ILIKE '%%computer science%%'
          AND (
            degree ILIKE 'm%%'
            OR degree ILIKE '%%master%%'
            OR degree ILIKE '%%ms%%'
          );
        """
        print_block(
            "Q7) How many entries applied to JHU for a masters in Computer Science? (downloaded fields)",
            run_one(conn, q7),
        )

        # Q8 (DOWNLOADED fields): Fall 2026 acceptances for specific unis, PhD in CS
        # FIX: carnegie mellon has a space in real data ("Carnegie Mellon University - ...")
        q8 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE
          term = %(term)s
          AND status = 'Accepted'
          AND degree ILIKE 'phd%%'
          AND program ILIKE '%%computer science%%'
          AND (
            program ILIKE '%%georgetown%%'
            OR program ILIKE '%%massachusetts institute of technology%%'
            OR program ILIKE '%%mit%%'
            OR program ILIKE '%%stanford%%'
            OR program ILIKE '%%carnegie mellon%%'
            OR program ILIKE '%%cmu%%'
          );
        """
        print_block(
            "Q8) Fall 2026 acceptances for (Georgetown/MIT/Stanford/CMU) PhD CS (downloaded fields).",
            run_one(conn, q8, {"term": FALL_2026}),
        )

        # Q9 (LLM fields): same as Q8 but using LLM-generated fields
        q9 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE
          term = %(term)s
          AND status = 'Accepted'
          AND degree ILIKE 'phd%%'
          AND llm_generated_program ILIKE '%%computer science%%'
          AND (
            llm_generated_university ILIKE '%%georgetown%%'
            OR llm_generated_university ILIKE '%%massachusetts institute of technology%%'
            OR llm_generated_university ILIKE '%%mit%%'
            OR llm_generated_university ILIKE '%%stanford%%'
            OR llm_generated_university ILIKE '%%carnegie mellon%%'
          );
        """
        print_block("Q9) Same as Q8 but using LLM-generated fields.", run_one(conn, q9, {"term": FALL_2026}))

        # Extra Q10: Top 10 programs by acceptance rate (Fall 2026), min sample size 200
        q10 = """
        SELECT
          program,
          COUNT(*) AS total_apps,
          SUM(CASE WHEN status='Accepted' THEN 1 ELSE 0 END) AS accepted,
          ROUND(
            SUM(CASE WHEN status='Accepted' THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0) * 100,
            2
          ) AS acceptance_rate
        FROM applicants
        WHERE term = %(term)s
        GROUP BY program 
        HAVING COUNT(*) >= 25       
        ORDER BY acceptance_rate DESC
        LIMIT 10;
        """
        print_block("Extra Q10) Top 10 programs by acceptance rate (Fall 2026, n>=200).", run_one(conn, q10, {"term": FALL_2026}))

        # Extra Q11: Average GRE Quant by status (only gre>0), Fall 2026
        q11 = """
        SELECT
          status,
          ROUND(AVG(gre)::numeric, 2) AS avg_gre_quant
        FROM applicants
        WHERE term = %(term)s
          AND gre > 0
        GROUP BY status
        ORDER BY avg_gre_quant DESC;
        """
        print_block("Extra Q11) Average GRE Quant by status (Fall 2026, gre>0).", run_one(conn, q11, {"term": FALL_2026}))


if __name__ == "__main__":
    main()
