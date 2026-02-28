"""
publisher.py

RabbitMQ publisher used by the Flask web tier.

Responsibilities:
- Open a connection/channel using RABBITMQ_URL.
- Declare durable exchange/queue/binding (idempotent).
- Publish persistent JSON tasks to RabbitMQ so the web app can return quickly.

Contract (per assignment):
- _open_channel() -> (conn, ch)
- publish_task(kind: str, payload: dict | None = None, headers: dict | None = None) -> None
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Tuple

import pika

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


def _open_channel() -> Tuple[pika.BlockingConnection, pika.adapters.blocking_connection.BlockingChannel]:
    """
    Open a RabbitMQ connection/channel and declare durable entities.

    Reads:
        RABBITMQ_URL from environment (e.g., amqp://guest:guest@rabbitmq:5672/%2F)

    Creates (idempotent):
        - durable direct exchange: tasks
        - durable queue: tasks_q
        - binding with routing key: tasks

    Returns:
        (connection, channel)

    Notes:
        - Declarations are durable to survive broker restarts.
        - Callers MUST close the returned connection.
    """
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)

    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)

    # Optional: enable publisher confirms for stronger delivery semantics.
    # ch.confirm_delivery()

    return conn, ch


def publish_task(kind: str, payload: dict | None = None, headers: dict | None = None) -> None:
    """
    Publish a durable task message to RabbitMQ.

    Message JSON keys:
        - kind: task identifier (e.g., "scrape_new_data", "recompute_analytics")
        - ts: UTC ISO timestamp
        - payload: dict (defaults to {})

    Delivery:
        - exchange: tasks
        - routing key: tasks
        - delivery_mode=2 (persistent)

    Raises:
        Exception on any failure so the Flask endpoint can return 503.
    """
    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    conn, ch = _open_channel()
    try:
        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                headers=headers or {},
                content_type="application/json",
            ),
            mandatory=False,
        )

        # If using confirms:
        # if not ch.wait_for_confirms():
        #     raise RuntimeError("Publish not confirmed")

    finally:
        conn.close()