"""Base engine template for individual transformation engines."""

from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


_LOGGER = logging.getLogger("Engines")
_LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - Engines - %(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False


class Engine(ABC):
    """Base template for individual transformation engines."""

    def __init__(self, queue: Any) -> None:
        if not hasattr(queue, "push_back") or not callable(queue.push_back):
            raise TypeError("Queue must provide a callable push_back method")
        self._queue = queue

    @property
    def queue(self) -> Any:
        """Return the configured queue."""
        return self._queue

    @abstractmethod
    def transform(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Apply a transformation to a read-only payload and return a dictionary."""
        raise NotImplementedError


__all__ = ["Engine"]
