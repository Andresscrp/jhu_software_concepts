# module_6/src/db_init.Dockerfile
FROM python:3.12-slim

WORKDIR /app

# install deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy your module_6 src/
COPY src/ /app/src/

# make imports predictable if you use them
ENV PYTHONPATH=/app

# default (compose overrides command anyway)
CMD ["python", "/app/src/load_data.py"]