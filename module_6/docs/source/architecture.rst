Architecture
============

Web (Flask)
-----------
- Serves the /analysis page
- Exposes POST endpoints for pull and update actions
- Uses a lock/busy mechanism to prevent concurrent pulls

ETL + DB
--------
- scrape.py: gather raw GradCafe data
- clean.py: normalize/clean fields
- load_data.py: insert into PostgreSQL with uniqueness policy
- query_data.py: query helpers used by analysis rendering
