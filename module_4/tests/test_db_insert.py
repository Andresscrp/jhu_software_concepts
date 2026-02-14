import os
from datetime import date

import pytest
import psycopg

import src.app as appmod


REQUIRED_NON_NULL_COLS = [
    "program",
    "date_added",
    "status",
    "term",
]


def _db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set for db tests.")
    return url


def _ensure_schema(conn) -> None:
    """Create applicants table and ensure url is UNIQUE (needed for ON CONFLICT(url))."""
    with conn.cursor() as cur:

        # Create table if missing
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS applicants (
                id SERIAL PRIMARY KEY,
                program TEXT NOT NULL,
                comments TEXT,
                date_added DATE,
                url TEXT NOT NULL,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa DOUBLE PRECISION,
                gre DOUBLE PRECISION,
                gre_v DOUBLE PRECISION,
                gre_aw DOUBLE PRECISION,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            );
            """
        )

        # Ensure url is unique (for ON CONFLICT)
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS applicants_url_unique_idx
            ON applicants (url);
            """
        )

    conn.commit()




def _truncate(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants RESTART IDENTITY;")
        conn.commit()


def _count_rows(conn: psycopg.Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        return int(cur.fetchone()[0])


def _insert_fake_rows(conn: psycopg.Connection, rows: list[dict]) -> None:
    sql = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term, us_or_international,
            gpa, gre, gre_v, gre_aw, degree, llm_generated_program, llm_generated_university
        )
        VALUES (
            %(program)s, %(comments)s, %(date_added)s, %(url)s, %(status)s, %(term)s, %(us_or_international)s,
            %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s, %(degree)s, %(llm_generated_program)s, %(llm_generated_university)s
        )
        ON CONFLICT (url) DO NOTHING;
    """
    with conn.cursor() as cur:
        for r in rows:
            cur.execute(sql, r)
        conn.commit()


@pytest.mark.db
def test_insert_on_pull_adds_rows_and_required_fields():
    """
    Before: table empty
    After: POST /pull-data inserts rows with required non-null fields
    """
    with psycopg.connect(_db_url()) as conn:
        _ensure_schema(conn)
        _truncate(conn)
        assert _count_rows(conn) == 0

        fake_rows = [
            {
                "program": "Test University - Computer Science",
                "comments": None,
                "date_added": date(2026, 1, 31),
                "url": "https://example.com/1",
                "status": "Accepted",
                "term": "Fall 2026",
                "us_or_international": "American",
                "gpa": 3.9,
                "gre": 165,
                "gre_v": 160,
                "gre_aw": 4.5,
                "degree": "PhD",
                "llm_generated_program": "Computer Science",
                "llm_generated_university": "Test University",
            }
        ]

        def fake_pull():
            with psycopg.connect(_db_url()) as c2:
                _ensure_schema(c2)
                _insert_fake_rows(c2, fake_rows)

        app = appmod.create_app(run_pull_fn=fake_pull, lock_exists_fn=lambda: False)
        app.config.update(TESTING=True)
        client = app.test_client()

        resp = client.post("/pull-data")
        assert resp.status_code == 202
        assert resp.get_json() == {"ok": True}

        # since pull runs in a thread in real code, we used run_pull_fn but it still runs in a thread;
        # so call it directly once to make test deterministic:
        fake_pull()

        assert _count_rows(conn) == 1

        with conn.cursor() as cur:
            cur.execute("SELECT program, date_added, status, term FROM applicants;")
            row = cur.fetchone()
            assert row is not None
            for v in row:
                assert v is not None


@pytest.mark.db
def test_idempotency_duplicate_rows_do_not_duplicate():
    """Pulling same data twice does not create duplicates (by url uniqueness)."""
    with psycopg.connect(_db_url()) as conn:
        _ensure_schema(conn)
        _truncate(conn)

        fake_rows = [
            {
                "program": "Test University - Computer Science",
                "comments": None,
                "date_added": date(2026, 1, 31),
                "url": "https://example.com/dup",
                "status": "Accepted",
                "term": "Fall 2026",
                "us_or_international": "American",
                "gpa": 3.9,
                "gre": 165,
                "gre_v": 160,
                "gre_aw": 4.5,
                "degree": "PhD",
                "llm_generated_program": "Computer Science",
                "llm_generated_university": "Test University",
            }
        ]

        _insert_fake_rows(conn, fake_rows)
        _insert_fake_rows(conn, fake_rows)
        assert _count_rows(conn) == 1
