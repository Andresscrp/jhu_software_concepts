import os
import psycopg

db_url = os.environ.get("DATABASE_URL")
print("DATABASE_URL =", db_url)

conn = psycopg.connect(db_url)
cur = conn.cursor()

cur.execute("select count(*) from applicants;")
print("total applicants =", cur.fetchone())

cur.execute("select term, count(*) from applicants group by term order by count(*) desc limit 15;")
print("top terms =", cur.fetchall())

cur.execute("select count(*) from applicants where term = %s;", ("Fall 2026",))
print("Fall 2026 =", cur.fetchone())

cur.close()
conn.close()
