FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root
USER 1000

# Wait script + run consumer
CMD ["sh", "-c", "python /app/src/worker/wait_for_rabbitmq.py && python -m src.worker.consumer"]