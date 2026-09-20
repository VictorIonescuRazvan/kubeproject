from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from fanout import FanoutService


def test_loads_consumers_from_yaml(tmp_path: Path) -> None:
    config = tmp_path / "consumers.yaml"
    config.write_text(
        """
consumers:
  - ip: 10.1.0.15
    port: 123
  - ip: 192.168.1.16
    port: 1012
""".strip(),
        encoding="utf-8",
    )

    service = FanoutService(config_path=str(config))

    assert [consumer.ip for consumer in service.consumers] == ["10.1.0.15", "192.168.1.16"]
    assert [consumer.port for consumer in service.consumers] == [123, 1012]


def test_forwards_requests_to_all_consumers() -> None:
    received: list[tuple[str, str]] = []
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            with lock:
                received.append((self.path, body.decode("utf-8")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args: object, **kwargs: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        service = FanoutService(config_path="/tmp/does-not-exist.yaml")
        service.consumers = [type("Consumer", (), {"ip": "127.0.0.1", "port": port, "url": f"http://127.0.0.1:{port}"})()]

        response = service.handle_request("POST", "/demo", {"Content-Type": "application/json"}, json.dumps({"hello": "world"}).encode("utf-8"))

        assert response.status_code == 200
        deadline = time.time() + 3
        while time.time() < deadline and len(received) < 1:
            time.sleep(0.05)

        assert len(received) == 1
        assert received[0][0] == "/demo"
        assert json.loads(received[0][1]) == {"hello": "world"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
