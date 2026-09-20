"""FastAPI-based sensor data aggregator."""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request as HttpRequest, urlopen

from auth import Auth
from engines import Engines
from message_queue import Queue

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

_LOGGER = logging.getLogger("Aggregator")
_LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - Aggregator - %(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False

app = FastAPI(title="Aggregator")

_QUEUE = Queue()
_AUTH = Auth(api_key=os.getenv("API_KEY", "test-api-key"))
_ENGINES = Engines(_QUEUE)
_STOP_EVENT = threading.Event()
_WORKER_THREAD: threading.Thread | None = None


def _mask_authorization(value: str) -> str:
    if value.lower().startswith("basic "):
        return "Basic <redacted>"
    if value.lower().startswith("bearer "):
        return "Bearer <redacted>"
    return "<redacted>"


async def _log_request(request: Request, payload: Any | None = None) -> None:
    if os.getenv("CONNECTION_LOGS") is None:
        _LOGGER.info("Received %s %s", request.method, request.url.path)
        return

    headers = dict(request.headers)
    if "authorization" in headers:
        headers["authorization"] = _mask_authorization(headers["authorization"])
    _LOGGER.info(
        "Received %s %s with headers=%s and payload=%s",
        request.method,
        request.url.path,
        headers,
        payload,
    )


async def _read_payload(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    if not raw_body:
        return {}
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    return payload


def _extract_basic_credential(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.lower().startswith("basic "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    encoded = authorization.split(" ", 1)[1]
    try:
        return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Malformed basic auth credential") from exc


def _destination_url() -> str:
    destination_ip = os.getenv("DESTINATION_IP", "localhost")
    destination_port = os.getenv("DESTINATION_PORT", "8080")
    return f"http://{destination_ip}:{destination_port}"


def _send_json(payload: dict[str, Any]) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    target = _destination_url()
    request = HttpRequest(
        target,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )
    _LOGGER.info("Sending data to message broker at %s", target)
    if os.getenv("CONNECTION_LOGS") is not None:
        _LOGGER.info("Broker payload payload=%s", payload)

    try:
        with urlopen(request, timeout=5) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            _LOGGER.info("Received broker response status=%s body=%s", response.status, response_body)
            return response.status, response_body
    except HTTPError as error:
        body_text = error.read().decode("utf-8", errors="replace")
        _LOGGER.error("Broker responded with HTTP %s: %s", error.code, body_text)
        raise RuntimeError(f"Broker returned HTTP {error.code}: {body_text}") from error
    except URLError as error:
        _LOGGER.error("Broker connection failed: %s", error.reason)
        raise RuntimeError(f"Broker connection failed: {error.reason}") from error


def _queue_worker() -> None:
    while not _STOP_EVENT.is_set():
        queued_item = _QUEUE.pop()
        if queued_item is None:
            time.sleep(5)
            continue

        _, payload = queued_item
        _LOGGER.info("Popped item from queue for delivery")
        try:
            _send_json(payload)
        except Exception as exc:  # pragma: no cover - failure handling is runtime behavior
            _LOGGER.error("Failed to publish queued item: %s", exc)
            try:
                _QUEUE.push_back(payload)
            except Exception:
                _LOGGER.exception("Unable to requeue payload after broker failure")
            time.sleep(1)


@app.on_event("startup")
def _startup() -> None:
    global _WORKER_THREAD
    _STOP_EVENT.clear()
    if _WORKER_THREAD is None or not _WORKER_THREAD.is_alive():
        _WORKER_THREAD = threading.Thread(target=_queue_worker, daemon=True, name="aggregator-queue-worker")
        _WORKER_THREAD.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    global _WORKER_THREAD
    _STOP_EVENT.set()
    if _WORKER_THREAD is not None:
        _WORKER_THREAD.join(timeout=5)
        _WORKER_THREAD = None


@app.post("/connect")
async def connect_endpoint(request: Request) -> dict[str, str]:
    payload = await _read_payload(request)
    await _log_request(request, payload)
    credential = _extract_basic_credential(request)
    token = _AUTH.get_token(credential)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"token": token}


@app.post("/publish")
async def publish_endpoint(request: Request) -> JSONResponse:
    payload = await _read_payload(request)
    await _log_request(request, payload)
    credential = _extract_basic_credential(request)
    if not _AUTH.auth(credential):
        raise HTTPException(status_code=401, detail="Invalid token")

    _LOGGER.info("Calling engines.transform for submitted payload")
    processed_payload = _ENGINES.transform(payload)
    _LOGGER.info("Engines.transform completed")
    return JSONResponse(status_code=202, content={"status": "accepted"})


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run("aggregator:app", host="0.0.0.0", port=8000, reload=False)


__all__ = ["app", "main"]
