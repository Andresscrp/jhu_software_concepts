"""
consumer.py

RabbitMQ worker that consumes tasks from a durable queue and performs
data-modifying work (scrape, recompute analytics) against Postgres.

Requirements (per assignment):
- Connect using RABBITMQ_URL.
- Declare durable exchange/queue/binding (idempotent).
- basic_qos(prefetch_count=1) for backpressure.
- Route by message["kind"] using a task map.
- Use DATABASE_URL for Postgres connection.
- Open a DB transaction per message; commit on success.
- Ack only after commit; on error rollback and nack(requeue=False).
- Implement:
    * handle_scrape_new_data(conn, payload)
    * handle_recompute_analytics(conn, payload)
- Maintain idempotence via ingestion_watermarks and ON CONFLICT DO NOTHING.
"""

from __future__ import annotations

import json
import os
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict

import pika
import psycopg
from psycopg import Connection

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


@dataclass(frozen=True)
class TaskMessage:
    """
    Parsed task message.

    Attributes:
        kind: Task identifier.
        ts: Timestamp string (UTC ISO).
        payload: Task-specific parameters (dict).
    """

    kind: str
    ts: str
    payload: Dict[str, Any]


def _declare_rabbitmq(ch: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """
    Declare durable AMQP entities (idempotent).

    Args:
        ch: RabbitMQ channel.
    """
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)


def _parse_message(body: bytes) -> TaskMessage:
    """
    Parse a RabbitMQ message body into a TaskMessage.

    Args:
        body: Raw bytes from RabbitMQ.

    Returns:
        Parsed TaskMessage.

    Raises:
        ValueError: if JSON is invalid or required keys are missing.
    """
    data = json.loads(body.decode("utf-8"))
    if "kind" not in data or "ts" not in data:
        raise ValueError("Message missing required keys: kind, ts")
    return TaskMessage(kind=data["kind"], ts=data["ts"], payload=data.get("payload") or {})


def _db_connect() -> Connection:
    """
    Connect to Postgres using DATABASE_URL.

    Returns:
        psycopg Connection.
    """
    db_url = os.environ["DATABASE_URL"]
    return psycopg.connect(db_url)


def _ensure_watermark_table(conn: Connection) -> None:
    """
    Ensure ingestion watermark table exists.

    This is used to process only new data and to make ingestion idempotent.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_watermarks (
                source      TEXT PRIMARY KEY,
                last_seen   TEXT,
                updated_at  TIMESTAMPTZ DEFAULT now()
            );
            """
        )


def _get_last_seen(conn: Connection, source: str) -> str | None:
    """
    Fetch the last_seen watermark for a given source.

    Args:
        conn: Open DB connection.
        source: Logical source name (e.g. "gradcafe").

    Returns:
        last_seen string or None if not present.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT last_seen FROM ingestion_watermarks WHERE source = %s;",
            (source,),
        )
        row = cur.fetchone()
    return row[0] if row else None


def _set_last_seen(conn: Connection, source: str, last_seen: str) -> None:
    """
    Upsert the last_seen watermark for a given source.

    Args:
        conn: Open DB connection.
        source: Logical source name.
        last_seen: New watermark value.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_watermarks (source, last_seen)
            VALUES (%s, %s)
            ON CONFLICT (source)
            DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = now();
            """,
            (source, last_seen),
        )


def handle_scrape_new_data(conn: Connection, payload: Dict[str, Any]) -> None:
    """
    Scrape and insert only new records since a watermark.

    Contract:
        - Read last_seen from DB unless payload["since"] provided.
        - Fetch only newer records.
        - Insert with parameterized SQL and idempotence:
            ON CONFLICT (ID_KEY) DO NOTHING (or equivalent)
        - Advance watermark to the max seen after successful insert.

    Notes:
        This function assumes you already have scraping/normalization code in:
            src/worker/etl/incremental_scraper.py (or similar)
        Replace the TODOs with your project's existing functions and schema.
    """
    source = payload.get("source", "gradcafe")
    since = payload.get("since")

    _ensure_watermark_table(conn)
    last_seen = since or _get_last_seen(conn, source)

    # ---- TODO: call YOUR incremental scraper here ----
    new_rows: list[dict[str, Any]] = []  # placeholder

    if not new_rows:
        return

    sort_key_name = payload.get("sort_key", "sort_key")
    max_seen = max(str(r[sort_key_name]) for r in new_rows if sort_key_name in r)

    # ---- TODO: insert into YOUR applicants table with ON CONFLICT DO NOTHING ----

    _set_last_seen(conn, source, max_seen)


def handle_recompute_analytics(conn: Connection, payload: Dict[str, Any]) -> None:
    """
    Recompute summaries/materialized views used by the UI.

    Contract:
        - Execute recompute logic in the same transaction as the message handling.
        - Commit on success only.

    Replace the SQL below with what your Module 3/5 app expects (e.g., refresh materialized
    views, rebuild summary tables, etc.).
    """
    with conn.cursor() as cur:
        # Example placeholder: refresh a materialized view if you have one.
        # cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY applicant_summary;")
        pass


def _task_map() -> Dict[str, Callable[[Connection, Dict[str, Any]], None]]:
    """
    Map task kinds to handler functions.

    Returns:
        Dict of kind -> handler(conn, payload)
    """
    return {
        "scrape_new_data": handle_scrape_new_data,
        "recompute_analytics": handle_recompute_analytics,
    }


def _on_message(
    ch: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    """
    RabbitMQ callback for each message.

    Behavior:
        - Parse JSON
        - Open DB transaction per message
        - Commit then ACK on success
        - Rollback and NACK(requeue=False) on error
    """
    try:
        msg = _parse_message(body)
        handlers = _task_map()
        if msg.kind not in handlers:
            raise ValueError(f"Unknown task kind: {msg.kind}")

        print(f"[worker] received kind={msg.kind} tag={method.delivery_tag}", flush=True)  # <-- ADDED

        with _db_connect() as conn:
            try:
                handlers[msg.kind](conn, msg.payload)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[worker] acked kind={msg.kind} tag={method.delivery_tag}", flush=True)  # <-- ADDED

    except Exception as e:
        print(f"[worker] ERROR: {e}", flush=True)  # <-- ADDED
        traceback.print_exc()  # <-- ADDED
        # No infinite retries per assignment.
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        print(f"[worker] nacked tag={method.delivery_tag} requeue=False", flush=True)  # <-- ADDED


def main() -> None:
    """
    Start the worker process and consume messages forever.
    """
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)

    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    _declare_rabbitmq(ch)
    ch.basic_qos(prefetch_count=1)

    print("[worker] connected; starting consume loop", flush=True)  # <-- ADDED
    ch.basic_consume(queue=QUEUE, on_message_callback=_on_message, auto_ack=False)
    try:
        ch.start_consuming()
    finally:
        conn.close()


if __name__ == "__main__":
    main()