FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY aggregator /app/aggregator
COPY lib /app/lib

WORKDIR /app/aggregator
RUN uv sync --frozen --no-dev

ENV API_KEY=test-api-key
ENV DESTINATION_IP=localhost
ENV DESTINATION_PORT=8080

EXPOSE 8000

CMD ["uv", "run", "--frozen", "aggregator"]
