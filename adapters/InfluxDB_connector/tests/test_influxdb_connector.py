from __future__ import annotations

import influxdb_connector as connector_module
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

from fastapi.testclient import TestClient
import pytest

from influxdb_connector import InfluxDBConfig, InfluxDBConnector, to_line_protocol


def test_to_line_protocol_escapes_tags_and_string_field() -> None:
    payload = {
        "pod": "pod,a =",
        "namespace": "ns x",
        "data": 'say "hi"\\path\nnext',
    }

    assert to_line_protocol(payload) == r'logs,pod=pod\,a\ \=,namespace=ns\ x data="say \"hi\"\\path\nnext"'


def test_to_line_protocol_rejects_missing_or_non_text_fields() -> None:
    with pytest.raises(ValueError, match="'data' must be a string"):
        to_line_protocol({"pod": "pod", "namespace": "ns", "data": 42})


def test_connector_writes_line_protocol_with_authentication(caplog: pytest.LogCaptureFixture) -> None:
    received: dict[str, object] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            received["path"] = self.path
            received["authorization"] = self.headers.get("Authorization")
            length = int(self.headers["Content-Length"])
            received["body"] = self.rfile.read(length).decode("utf-8")
            self.send_response(204)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connector = InfluxDBConnector(
            InfluxDBConfig(
                host="127.0.0.1",
                port=port,
                org="my org",
                bucket="my bucket",
                token="influxdb-connector-token",
            )
        )
        with caplog.at_level("INFO", logger="InfluxDBConnector"):
            connector.write({"pod": "pod", "namespace": "ns", "data": "ok"})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert received == {
        "path": "/api/v2/write?org=my+org&bucket=my+bucket&precision=ns",
        "authorization": "Token influxdb-connector-token",
        "body": 'logs,pod=pod,namespace=ns data="ok"',
    }
    assert "Successfully pushed data to InfluxDB status=204" in caplog.text
    assert "data=\"ok\"" not in caplog.text


def test_fastapi_app_accepts_json_and_returns_no_content(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[dict[str, str]] = []

    class Connector:
        def write(self, payload: dict[str, str]) -> None:
            received.append(payload)

    monkeypatch.setattr(connector_module, "_CONNECTOR", Connector())

    with TestClient(connector_module.app) as client:
        response = client.post(
            "/",
            json={"pod": "pod", "namespace": "ns", "data": "ok"},
        )

    assert response.status_code == 204
    assert received == [{"pod": "pod", "namespace": "ns", "data": "ok"}]
