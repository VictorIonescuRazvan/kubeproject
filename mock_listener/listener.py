#!/usr/bin/env python3

import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockListenerHandler(BaseHTTPRequestHandler):
    def _write_stdout(self, message: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"{timestamp} {message}", flush=True)

    def _write_request(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        self._write_stdout("-" * 30)
        self._write_stdout(f"{self.command} {self.path} {self.request_version}")
        self._write_stdout(str(self.headers).rstrip())
        if body:
            sys.stdout.buffer.write(body)
            sys.stdout.buffer.write(b"\n")
            sys.stdout.flush()

    def _respond(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK\n")

    def do_GET(self) -> None:
        self._write_request()
        self._respond()

    def do_POST(self) -> None:
        self._write_request()
        self._respond()

    def do_PUT(self) -> None:
        self._write_request()
        self._respond()

    def do_PATCH(self) -> None:
        self._write_request()
        self._respond()

    def do_DELETE(self) -> None:
        self._write_request()
        self._respond()

    def do_OPTIONS(self) -> None:
        self._write_request()
        self._respond()

    def do_HEAD(self) -> None:
        self._write_request()
        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        self._write_stdout(format % args)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8080), MockListenerHandler)
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"{timestamp} Mock HTTP listener listening on port 8080", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()