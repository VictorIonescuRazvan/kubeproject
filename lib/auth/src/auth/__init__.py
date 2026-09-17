"""API-key authentication and expiring UUID7 token management."""

from __future__ import annotations

import heapq
import logging
import os
import secrets
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone


_LOGGER = logging.getLogger("auth")
_LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - Auth - %(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False

_DEFAULT_TOKEN_EXPIRATION = 300.0
_API_KEY_ENVIRONMENT_VARIABLE = "API_KEY"
_TOKEN_EXPIRATION_ENVIRONMENT_VARIABLES = ("TOKEN_EXPIRATION", "TOKEN_EXPIRY")


class Auth:
    """Authenticate API keys and issue short-lived UUID7 bearer tokens."""

    def __init__(
        self,
        api_key: str | None = None,
        token_expiration: float | None = None,
        *,
        expiration: float | None = None,
    ) -> None:
        if token_expiration is not None and expiration is not None:
            raise ValueError("Specify only one token expiration value")

        self._api_key = api_key if api_key is not None else os.getenv(_API_KEY_ENVIRONMENT_VARIABLE)
        if self._api_key is None:
            raise ValueError(f"{_API_KEY_ENVIRONMENT_VARIABLE} is not configured")

        configured_expiration = token_expiration if token_expiration is not None else expiration
        if configured_expiration is None:
            configured_expiration = self._expiration_from_environment()
        if configured_expiration <= 0:
            raise ValueError("Token expiration must be greater than zero")

        self._token_expiration = float(configured_expiration)
        self._tokens: dict[str, datetime] = {}
        self._expiration_queue: list[tuple[datetime, str]] = []
        self._lock = threading.RLock()

    @staticmethod
    def _expiration_from_environment() -> float:
        for variable in _TOKEN_EXPIRATION_ENVIRONMENT_VARIABLES:
            value = os.getenv(variable)
            if value is not None:
                try:
                    return float(value)
                except ValueError as error:
                    raise ValueError(f"{variable} must be a number of seconds") from error
        return _DEFAULT_TOKEN_EXPIRATION

    def _remove_expired(self, now: datetime) -> None:
        while self._expiration_queue and self._expiration_queue[0][0] <= now:
            expiry, token = heapq.heappop(self._expiration_queue)
            if self._tokens.get(token) == expiry:
                del self._tokens[token]

    def get_token(self, api_key: str) -> str | None:
        """Return a token for a valid API key, or ``None`` otherwise."""
        _LOGGER.info("Starting get_token")
        with self._lock:
            now = datetime.now(timezone.utc)
            self._remove_expired(now)
            if not secrets.compare_digest(api_key, self._api_key):
                _LOGGER.info("Finished get_token: invalid API key")
                return None

            token = str(uuid.uuid7())
            expiry = now + timedelta(seconds=self._token_expiration)
            self._tokens[token] = expiry
            heapq.heappush(self._expiration_queue, (expiry, token))
            _LOGGER.info("Finished get_token: token issued")
            return token

    def auth(self, token: str) -> bool:
        """Return whether a token is currently valid."""
        _LOGGER.info("Starting auth")
        with self._lock:
            now = datetime.now(timezone.utc)
            self._remove_expired(now)
            valid = token in self._tokens
        _LOGGER.info("Finished auth: %s", "valid token" if valid else "invalid token")
        return valid


Authenticator = Auth

__all__ = ["Auth", "Authenticator"]
