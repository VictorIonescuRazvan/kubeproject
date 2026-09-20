"""HTTP fanout service forwarding received requests to configured consumers."""

from __future__ import annotations

import logging
import os
import sys
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

_LOGGER = logging.getLogger("Fanout")
_LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - Fanout - %(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False


@dataclass(frozen=True)
class Consumer:
    """A configured HTTP consumer endpoint."""

    ip: str
    port: int

    @property
    def url(self) -> str:
        return f"http://{self.ip}:{self.port}"


class _Response:
    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body


class FanoutService:
    """Handle incoming requests and forward copies to all configured consumers."""

    def __init__(self, config_path: str = "/etc/consumers.yaml") -> None:
        self._config_path = config_path
        self._consumers: list[Consumer] = []
        self.reload()

    @property
    def consumers(self) -> list[Consumer]:
        return list(self._consumers)

    @consumers.setter
    def consumers(self, value: list[Consumer]) -> None:
        self._consumers = list(value)

    def reload(self) -> None:
        self._consumers = self._load_consumers(self._config_path)

    @staticmethod
    def _load_consumers(config_path: str) -> list[Consumer]:
        try:
            with open(config_path, encoding="utf-8") as config_file:
                loaded = yaml.safe_load(config_file) or {}
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Consumer config file not found: {config_path}") from exc
        except OSError as exc:
            raise OSError(f"Unable to read consumer config: {config_path}") from exc

        if not isinstance(loaded, dict):
            raise ValueError("Consumer config must be a mapping")

        entries = loaded.get("consumers", [])
        if not isinstance(entries, list):
            raise ValueError("Consumer config 'consumers' must be a list")

        consumers: list[Consumer] = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"Consumer entry {index} must be a mapping")

            ip = str(entry.get("ip", "")).strip()
            port = entry.get("port")
            if not ip:
                raise ValueError(f"Consumer entry {index} is missing an IP address")
            if port is None:
                raise ValueError(f"Consumer entry {index} is missing a port")

            try:
                port_number = int(port)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Consumer entry {index} port must be an integer") from exc

            if port_number <= 0:
                raise ValueError(f"Consumer entry {index} port must be greater than zero")

            consumers.append(Consumer(ip=ip, port=port_number))

        return consumers

    def handle_request(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str] | None,
        body: bytes,
    ) -> _Response:
        if not self._consumers:
            _LOGGER.warning("No consumers configured for fanout request %s %s", method, path)
            return _Response(202, "accepted")

        forwarded_headers = dict(headers or {})
        forwarded_headers.pop("Host", None)
        forwarded_headers.pop("Content-Length", None)

        def _forward(consumer: Consumer) -> None:
            target_url = f"{consumer.url}{path}"
            request = Request(target_url, data=body, headers=forwarded_headers, method=method)
            try:
                with urlopen(request, timeout=5) as response:
                    status = response.getcode()
                    response_body = response.read().decode("utf-8", errors="replace")
                    if status >= 400:
                        _LOGGER.error(
                            "Forward to %s failed with HTTP %s: %s",
                            consumer.url,
                            status,
                            response_body or "<empty response>",
                        )
            except HTTPError as error:
                response_body = error.read().decode("utf-8", errors="replace")
                _LOGGER.error(
                    "Forward to %s failed with HTTP %s: %s",
                    consumer.url,
                    error.code,
                    response_body or "<empty response>",
                )
            except URLError as error:
                _LOGGER.exception("Forward to %s could not be made: %s", consumer.url, error.reason)
            except Exception:
                _LOGGER.exception("Unexpected error forwarding to %s", consumer.url)

        for consumer in self._consumers:
            thread = threading.Thread(target=_forward, args=(consumer,), daemon=True)
            thread.start()

        return _Response(202, "accepted")


class FanoutHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], service: FanoutService) -> None:
        self.service = service
        super().__init__(server_address, FanoutRequestHandler)


class FanoutRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self._handle_request()

    def do_POST(self) -> None:  # noqa: N802
        self._handle_request()

    def do_PUT(self) -> None:  # noqa: N802
        self._handle_request()

    def do_PATCH(self) -> None:  # noqa: N802
        self._handle_request()

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle_request()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._handle_request()

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle_request()

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle_request(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(content_length) if content_length > 0 else b""

        service: FanoutService = self.server.service
        response = service.handle_request(
            method=self.command,
            path=self.path,
            headers=dict(self.headers.items()),
            body=body,
        )

        self.send_response(response.status_code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        if response.body:
            self.wfile.write(response.body.encode("utf-8"))


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    config_path = os.getenv("CONSUMERS_CONFIG_PATH", "/etc/consumers.yaml")
    service = FanoutService(config_path=config_path)
    server = FanoutHTTPServer((host, port), service)
    _LOGGER.info("Fanout service listening on %s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


__all__ = ["Consumer", "FanoutHTTPServer", "FanoutRequestHandler", "FanoutService", "main"]
