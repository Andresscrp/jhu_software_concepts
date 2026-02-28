import os
from unittest.mock import MagicMock, patch

import pytest

from src.web import publisher


def test_open_channel_declares_durable_entities(monkeypatch):
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")

    fake_conn = MagicMock()
    fake_ch = MagicMock()
    fake_conn.channel.return_value = fake_ch

    with patch("src.web.publisher.pika.URLParameters") as mock_params, \
         patch("src.web.publisher.pika.BlockingConnection", return_value=fake_conn) as mock_conn:

        conn, ch = publisher._open_channel()

        mock_params.assert_called_once()
        mock_conn.assert_called_once()

        fake_ch.exchange_declare.assert_called_once_with(
            exchange=publisher.EXCHANGE, exchange_type="direct", durable=True
        )
        fake_ch.queue_declare.assert_called_once_with(queue=publisher.QUEUE, durable=True)
        fake_ch.queue_bind.assert_called_once_with(
            exchange=publisher.EXCHANGE, queue=publisher.QUEUE, routing_key=publisher.ROUTING_KEY
        )

        assert conn is fake_conn
        assert ch is fake_ch


def test_publish_task_calls_basic_publish_and_closes_connection(monkeypatch):
    fake_conn = MagicMock()
    fake_ch = MagicMock()

    with patch("src.web.publisher._open_channel", return_value=(fake_conn, fake_ch)):

        publisher.publish_task("scrape_new_data", payload={"x": 1}, headers={"h": "v"})

        # basic_publish called
        assert fake_ch.basic_publish.call_count == 1
        kwargs = fake_ch.basic_publish.call_args.kwargs

        assert kwargs["exchange"] == publisher.EXCHANGE
        assert kwargs["routing_key"] == publisher.ROUTING_KEY
        assert kwargs["mandatory"] is False

        # verify properties include persistence + json content type
        props = kwargs["properties"]
        assert props.delivery_mode == 2
        assert props.content_type == "application/json"
        assert props.headers == {"h": "v"}

        # ALWAYS closes connection
        fake_conn.close.assert_called_once()


def test_publish_task_defaults_payload_and_headers(monkeypatch):
    fake_conn = MagicMock()
    fake_ch = MagicMock()

    with patch("src.web.publisher._open_channel", return_value=(fake_conn, fake_ch)):

        publisher.publish_task("recompute_analytics")

        kwargs = fake_ch.basic_publish.call_args.kwargs
        props = kwargs["properties"]
        assert props.headers == {}
        fake_conn.close.assert_called_once()


def test_publish_task_closes_connection_on_publish_error(monkeypatch):
    fake_conn = MagicMock()
    fake_ch = MagicMock()
    fake_ch.basic_publish.side_effect = RuntimeError("boom")

    with patch("src.web.publisher._open_channel", return_value=(fake_conn, fake_ch)):

        with pytest.raises(RuntimeError):
            publisher.publish_task("recompute_analytics")

        # even on error, close runs
        fake_conn.close.assert_called_once()