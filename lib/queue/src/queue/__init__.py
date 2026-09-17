"""Thread-safe, timestamp-prioritized object queue."""

from __future__ import annotations

import heapq
import threading
from datetime import datetime, timezone
from typing import Any


class _Entry:
    __slots__ = ("timestamp", "item")

    def __init__(self, timestamp: datetime, item: Any) -> None:
        self.timestamp = timestamp
        self.item = item

    def __lt__(self, other: _Entry) -> bool:
        return self.timestamp < other.timestamp


class Queue:
    """Store objects in earliest-first timestamp order.
    """

    def __init__(self) -> None:
        self._items: list[_Entry] = []
        self._lock = threading.RLock()

    def push_back(self, item: Any) -> None:
        """Add an item with the current UTC timestamp."""
        timestamp = datetime.now(timezone.utc)
        with self._lock:
            heapq.heappush(self._items, _Entry(timestamp, item))

    def pop(self) -> tuple[datetime, Any] | None:
        """Remove and return the newest ``(timestamp, item)`` pair."""
        with self._lock:
            if not self._items:
                return None
            entry = heapq.heappop(self._items)
            return entry.timestamp, entry.item

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


PriorityQueue = Queue

__all__ = ["PriorityQueue", "Queue"]
