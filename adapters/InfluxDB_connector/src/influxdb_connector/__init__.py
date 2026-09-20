"""HTTP adapter that writes JSON payloads to InfluxDB using line protocol."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

_LOGGER = logging.getLogger("InfluxDBConnector")
app = FastAPI(title="InfluxDB Connector")


@dataclass(frozen=True)
class InfluxDBConfig:
    """Connection and line protocol settings for InfluxDB."""

    host: str
    port: int
    org: str
    bucket: str
    token: str = "influxdb-connector-token"
    measurement: str = "logs"

    @classmethod
    def from_env(cls) -> InfluxDBConfig:
        return cls(
            host=os.getenv("INFLUXDB_HOST", "localhost"),
            port=int(os.getenv("INFLUXDB_PORT", "8086")),
            org=os.getenv("INFLUXDB_ORG", "default-org"),
            bucket=os.getenv("INFLUXDB_BUCKET", "default-bucket"),
            token=os.getenv("INFLUXDB_TOKEN", "influxdb-connector-token"),
            measurement=os.getenv("INFLUXDB_MEASUREMENT", "logs"),
        )

    @property
    def write_url(self) -> str:
        query = urlencode({"org": self.org, "bucket": self.bucket, "precision": "ns"})
        return f"http://{self.host}:{self.port}/api/v2/write?{query}"


def _escape_tag_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(" ", "\\ ")
        .replace("=", "\\=")
    )


def _escape_measurement(value: str) -> str:
    return _escape_tag_value(value)


def _escape_field_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
    return '"' + escaped.replace('"', '\\"') + '"'


def to_line_protocol(payload: dict[str, Any], measurement: str = "logs") -> str:
    """Convert the connector payload to one InfluxDB line protocol record."""
    for field in ("pod", "namespace", "data"):
        if field not in payload or not isinstance(payload[field], str):
            raise ValueError(f"'{field}' must be a string")

    tags = ",".join(
        f"{name}={_escape_tag_value(payload[name])}"
        for name in ("pod", "namespace")
    )
    return f"{_escape_measurement(measurement)},{tags} data={_escape_field_value(payload['data'])}"


class InfluxDBConnector:
    """Convert incoming payloads and deliver them to InfluxDB."""

    def __init__(self, config: InfluxDBConfig) -> None:
        self.config = config

    def write(self, payload: dict[str, Any]) -> None:
        body = to_line_protocol(payload, self.config.measurement).encode("utf-8")
        request = Request(
            self.config.write_url,
            data=body,
            headers={
                "Authorization": f"Token {self.config.token}",
                "Content-Type": "text/plain; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                response.read()
                _LOGGER.info(
                    "Successfully pushed data to InfluxDB status=%s destination=%s",
                    response.status,
                    request.full_url,
                )
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"InfluxDB returned HTTP {exc.code}: {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"Unable to connect to InfluxDB: {exc.reason}") from exc


class InfluxDBPayload(BaseModel):
    """JSON payload accepted by the connector."""

    pod: str
    namespace: str
    data: str


_CONNECTOR = InfluxDBConnector(InfluxDBConfig.from_env())


@app.post("/", status_code=204)
def write_payload(payload: InfluxDBPayload) -> None:
    """Convert and write one payload to InfluxDB."""
    try:
        _CONNECTOR.write(payload.model_dump())
    except RuntimeError as exc:
        _LOGGER.error("InfluxDB write failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def main() -> None:
    """Run the FastAPI application with uvicorn."""
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


__all__ = [
    "InfluxDBConfig",
    "InfluxDBConnector",
    "InfluxDBPayload",
    "app",
    "main",
    "to_line_protocol",
    "write_payload",
]
