FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY sample_apps /app/sample_apps

CMD ["uv", "run", "--frozen", "python", "/app/sample_apps/intermittent_failures.py"]
