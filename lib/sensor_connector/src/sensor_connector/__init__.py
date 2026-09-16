"""HTTP connector used by sensors to communicate with an aggregator."""

from __future__ import annotations

import base64
import json
import logging
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


_LOGGER = logging.getLogger("sensor_connector")
_LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - sensor_connector - %(message)s")
    )
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False


class ConnectorError(Exception):
    """Base exception for connector failures."""


class InvalidCredentialsError(ConnectorError):
    """The aggregator rejected the supplied credentials."""


class BadRequestError(ConnectorError):
    """The aggregator rejected a request as invalid."""


class ServerError(ConnectorError):
    """The aggregator reported an internal failure."""


class SensorConnector:
    """Authenticate with an aggregator and publish sensor data to it."""

    def __init__(
        self,
        *,
        connect_endpoint: str = "/connect",
        publish_endpoint: str = "/publish",
        timeout: float = 30.0,
    ) -> None:
        self._connect_endpoint = connect_endpoint
        self._publish_endpoint = publish_endpoint
        self._timeout = timeout
        self._token: str | None = None
        self._last_address: str | None = None
        self._api_key: str | None = None
        self._context: str | None = None

    @property
    def token(self) -> str | None:
        """Return the current authentication token."""
        return self._token

    @property
    def last_address(self) -> str | None:
        """Return the address used by the most recent connection."""
        return self._last_address

    def connect(self, api_key: str, context: str, hostname: str) -> str:
        """Authenticate and return the token issued by the aggregator."""
        self._api_key = api_key
        self._context = context
        self._last_address = hostname
        address = self._url(hostname, self._connect_endpoint)
        payload = {"uuid": str(uuid4()), "context": context}
        _LOGGER.info("Connecting to %s", hostname)

        response = self._request(address, payload, api_key)
        if response.status == 200:
            try:
                token = json.loads(response.body)["token"]
            except (KeyError, TypeError, json.JSONDecodeError) as error:
                raise ConnectorError("Authentication response did not contain a token") from error
            if not isinstance(token, str) or not token:
                raise ConnectorError("Authentication response did not contain a valid token")
            self._token = token
            _LOGGER.info("Successfully connected to %s", hostname)
            return token

        self._raise_for_status(response.status, response.body, "authentication")
        raise AssertionError("unreachable")

    def publish(self, data: dict[str, Any]) -> None:
        """Publish a data dictionary, reconnecting once after an expired token."""
        if self._token is None or self._last_address is None or self._api_key is None:
            raise ConnectorError("Connect before publishing data")

        address = self._url(self._last_address, self._publish_endpoint)
        _LOGGER.info("Submitting data to %s", self._last_address)
        response = self._request(address, data, self._token)
        if response.status == 401:
            if self._context is None:
                raise InvalidCredentialsError("Authentication failed and connection context is unavailable")
            self.connect(self._api_key, self._context, self._last_address)
            response = self._request(address, data, self._token)

        if response.status == 202:
            _LOGGER.info("Successfully sent data to %s", self._last_address)
            return

        self._raise_for_status(response.status, response.body, "publishing")

    def _request(self, address: str, payload: dict[str, Any], credential: str) -> "_Response":
        request = Request(
            address,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Basic "
                + base64.b64encode(credential.encode("utf-8")).decode("ascii"),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return _Response(response.status, response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            _LOGGER.info("Failed request to %s with HTTP %s and message %s", address, error.code, body)
            return _Response(error.code, body)
        except URLError as error:
            _LOGGER.info("Failed request to %s with error %s", address, error.reason)
            raise ConnectorError(f"Unable to reach aggregator: {error.reason}") from error

    @staticmethod
    def _url(hostname: str, endpoint: str) -> str:
        return hostname.rstrip("/") + "/" + endpoint.lstrip("/")

    @staticmethod
    def _raise_for_status(status: int, body: str, operation: str) -> None:
        if status == 400:
            if operation == "publishing":
                raise BadRequestError(body)
            raise ConnectorError("Bad request while authenticating")
        if status == 401:
            raise InvalidCredentialsError("Invalid credentials")
        if status == 500:
            raise ServerError(f"Aggregator server error while {operation}: {body}")
        raise ConnectorError(f"Unexpected HTTP status {status} while {operation}: {body}")


class _Response:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body


__all__ = [
    "BadRequestError",
    "ConnectorError",
    "InvalidCredentialsError",
    "SensorConnector",
    "ServerError",
]
