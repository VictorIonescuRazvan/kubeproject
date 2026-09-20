FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY mock_listener/listener.py /app/listener.py

EXPOSE 8080

CMD ["python", "/app/listener.py"]