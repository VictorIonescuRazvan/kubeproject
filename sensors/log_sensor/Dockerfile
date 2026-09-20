FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY sensors /app/sensors
COPY lib /app/lib

WORKDIR /app/sensors/log_sensor
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "--frozen", "log-sensor"]
