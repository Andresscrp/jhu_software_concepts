"""
load_data.py

I load my cleaned GradCafe data into the PostgreSQL applicants table.
"""

import json
import psycopg
import os

# Database connection config
DB_NAME = "module_3db"
DB_USER = "postgres"
DB_PASSWORD = os.environ.get("PGPASSWORD")
DB_HOST = "localhost"
DB_PORT = 5432


INPUT_JSON = "../module_2/cleaned_applicant_data.json"


def main():

    # Load cleaned JSON data
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Connect to Postgres
    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

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
            %(us_or_int)s,
            %(gpa)s,
            %(gre)s,
            %(gre_v)s,
            %(gre_aw)s,
            %(degree)s,
            %(llm_prog)s,
            %(llm_uni)s
        );
    """


    with conn:
        with conn.cursor() as cur:
            cur.execute("SET datestyle TO 'ISO, DMY';")

            for row in records:

                data = {
                    "program": row.get("program"),
                    "comments": row.get("notes"),
                    "date_added": row.get("notification_date"),
                    "url": row.get("url"),
                    "status": row.get("decision"),
                    "term": None,
                    "us_or_int": row.get("country_of_origin"),
                    "gpa": row.get("undergrad_gpa"),
                    "gre": row.get("gre_general"),
                    "gre_v": row.get("gre_verbal"),
                    "gre_aw": row.get("gre_aw"),
                    "degree": row.get("degree"),
                    "llm_prog": None,
                    "llm_uni": row.get("institution"),
                }

                cur.execute(insert_sql, data)


    conn.close()

    print(f"Inserted {len(records)} rows into applicants.")


if __name__ == "__main__":
    main()
