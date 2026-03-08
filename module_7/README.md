# Module 6 — Deploy Anywhere (Docker Compose + RabbitMQ Microservices)

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** 605.256 Modern Software Concepts in Python  
**Module:** Module 6 — Deploy Anywhere

---

## Sources

- Course lecture materials  
- Docker documentation  
- Docker Compose documentation  
- RabbitMQ documentation  
- AMQP documentation  
- PostgreSQL documentation  
- Flask documentation  
- Psycopg documentation  
- Pytest documentation  
- Pylint documentation  
- ChatGPT  

---

## Overview

This module refactors the GradCafe Analytics system into a production-style microservice architecture using Docker Compose and RabbitMQ.

The system separates responsibilities into independent services:

- PostgreSQL (database)
- RabbitMQ (message broker)
- Flask **web** service (publishes tasks, returns fast)
- Background **worker** service (consumes tasks)
- One-time **db_init** loader that imports the dataset

All long-running or data-modifying operations are decoupled from HTTP requests and executed asynchronously through a durable RabbitMQ queue.

This architecture provides:

- Improved reliability (no request timeouts)
- Backpressure via message buffering
- At-least-once delivery semantics
- Transactional database commits
- Reproducible container builds
- Deployment parity across environments

The entire stack runs on a clean machine using:

docker compose up --build

---

## System Architecture

Client Browser  
        ↓  
Flask Web (Port 8080)  
        ↓ publish_task()  
RabbitMQ (Exchange: tasks, Queue: tasks_q)  
        ↓  
Worker (prefetch=1, manual ACK)  
        ↓  
PostgreSQL Database  

All write operations flow through RabbitMQ.  
The web tier remains stateless and responsive.

---

## What the Application Does

### Web Service

- GET `/analysis` — analytics dashboard  
- POST `/pull-data` — queues `"scrape_new_data"`  
- POST `/update-analysis` — queues `"recompute_analytics"`  

Each POST request returns:

```json
{"status":"queued","task":"<task_name>"}
```

with HTTP 202 Accepted.

---

### Worker Service

The worker:

- Connects using `RABBITMQ_URL`
- Declares durable exchange `tasks`
- Declares durable queue `tasks_q`
- Binds routing key `tasks`
- Uses `basic_qos(prefetch_count=1)`
- Routes by message `kind`
- Opens one database transaction per message
- Commits on success
- Acknowledges only after commit
- NACKs without requeue on failure

This ensures safe write paths and prevents infinite retry loops.

---

## Repository Structure

```
module_6/

docker-compose.yml
README.md
setup.py

src/
  web/
    Dockerfile
    requirements.txt
    publisher.py
    run.py
    app/

  worker/
    Dockerfile
    requirements.txt
    consumer.py
    wait_for_rabbitmq.py

  db/
    load_data.py

  data/
    llm_extend_applicant_data.json

tests/
docs/
```

---

## Services (docker-compose.yml)

### 1) db (PostgreSQL)

- Image: postgres:16  
- Database: gradcafe  
- Port: 5432:5432  
- Named Volume: pgdata  
- Healthcheck: pg_isready -U postgres -d gradcafe  

---

### 2) rabbitmq (RabbitMQ + Management UI)

- Image: rabbitmq:3-management  
- Ports:  
  - 5672 (AMQP)  
  - 15672 (Management UI)  
- Healthcheck: rabbitmq-diagnostics -q ping  

---

### 3) db_init (One-shot Loader)

- Runs: python /app/src/load_data.py  
- Imports ~49,960 records  
- Exits with code 0 on success  
- Ensures database ready before web/worker start  

---

### 4) web (Flask Tier)

- Port: 8080:8080  
- Runs: python -m src.app  
- Depends on healthy db + rabbitmq + completed db_init  
- Publishes tasks using src/web/publisher.py  

---

### 5) worker (Task Consumer)

- Runs: python -m src.worker.consumer  
- Executes as non-root (USER 1000)  
- Waits for RabbitMQ before starting  
- Consumes tasks and executes them  

---

## Environment Variables

### PostgreSQL

DATABASE_URL=postgresql://postgres:postgres@db:5432/gradcafe

### RabbitMQ

RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/%2F

---

## Running the System

From repository root:

docker compose down  
docker compose up --build  

Expected:

- db becomes healthy  
- rabbitmq becomes healthy  
- db_init loads dataset and exits 0  
- web starts on http://127.0.0.1:8080  
- worker begins consuming  

---

## Verifying End-to-End Operation

### 1) Web Running

Open:

http://127.0.0.1:8080

Redirects to `/analysis`.

---

### 2) Queueing Tasks

POST /pull-data  
POST /update-analysis  

Response:

{"status":"queued","task":"..."}

Status: 202 Accepted.

---

### 3) Worker Logs

docker compose logs -f worker

Expected output:

received kind=scrape_new_data  
acked kind=scrape_new_data  
received kind=recompute_analytics  
acked kind=recompute_analytics  

Confirms async pipeline works:

web → RabbitMQ → worker → PostgreSQL

---

### 4) RabbitMQ Management UI (Optional)

http://localhost:15672  

Login:  
guest  
guest  

---

## Docker Hub Publication

Local images:

jhu_software_concepts-web:latest  
jhu_software_concepts-worker:latest  

Push:

docker login  

docker tag jhu_software_concepts-web:latest andresscrp/jhu_web:latest  
docker tag jhu_software_concepts-worker:latest andresscrp/jhu_worker:latest  

docker push andresscrp/jhu_web:latest  
docker push andresscrp/jhu_worker:latest  

Repositories:

andresscrp/jhu_web  
andresscrp/jhu_worker  

---

## Testing

Run:

python -m pytest  

With coverage:

python -m pytest --cov=src --cov-report=term-missing  

Current coverage: ~92%

---

## Static Analysis

python -m pylint src --fail-under=10  

Target: 10.00/10  

---

## Software Assurance Properties

- Durable AMQP entities  
- Persistent messages (delivery_mode=2)  
- Idempotent queue declarations  
- Transaction-per-message DB handling  
- Manual acknowledgments  
- Parameterized SQL queries  
- Non-root container execution  
- Reproducible container builds  

---

## Final Deliverables

Submitted:

- module_6 zipped folder  
- Private GitHub repository link  
- Docker Hub repository links  
- PDF with required screenshots  
- pytest output  
- pylint output  

All rubric requirements satisfied.

---

## Notes

This module demonstrates:

- Microservice architecture  
- Asynchronous task processing  
- Container orchestration  
- Reliable messaging  
- Deployment reproducibility  

The application now runs “deploy anywhere” via Docker Compose.