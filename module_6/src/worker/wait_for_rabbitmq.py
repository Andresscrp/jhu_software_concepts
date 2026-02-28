import os
import socket
import time

host = os.getenv("RABBITMQ_HOST", "rabbitmq")
port = int(os.getenv("RABBITMQ_PORT", "5672"))
timeout_s = int(os.getenv("RABBITMQ_WAIT_SECONDS", "90"))

deadline = time.time() + timeout_s
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"RabbitMQ is reachable at {host}:{port}")
            raise SystemExit(0)
    except OSError:
        time.sleep(1)

print(f"ERROR: RabbitMQ not reachable at {host}:{port} after {timeout_s} seconds")
raise SystemExit(1)