FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY adapters/InfluxDB_connector /app/adapters/InfluxDB_connector

WORKDIR /app/adapters/InfluxDB_connector
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "--frozen", "influxdb-connector"]
