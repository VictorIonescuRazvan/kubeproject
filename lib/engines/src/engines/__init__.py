"""Engine templates and a sample transformer for queued sensor payloads."""

from __future__ import annotations

import logging
import sys
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any

from .engine import Engine
from .sample_engine import SampleEngine


_LOGGER = logging.getLogger("Engines")
_LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - Engines - %(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False


class Engines:
    """Run the configured Engine implementations in parallel against the same payload."""

    _ENGINE_CLASSES: list[type[Engine]] = [SampleEngine]

    def __init__(self, queue: Any) -> None:
        if not hasattr(queue, "push_back") or not callable(queue.push_back):
            raise TypeError("Queue must provide a callable push_back method")

        self._queue = queue
        self._engines: list[Engine] = []

        for engine_class in self._ENGINE_CLASSES:
            engine = engine_class(queue)
            if not isinstance(engine, Engine):
                raise TypeError("All configured engines must inherit from Engine")
            self._engines.append(engine)
            _LOGGER.info("Loaded engine: %s", engine.__class__.__module__)

    @property
    def queue(self) -> Any:
        return self._queue

    def transform(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not self._engines:
            return dict(payload)

        lock = Lock()
        results: list[dict[str, Any]] = []

        def _run(engine: Engine) -> dict[str, Any]:
            transformed = engine.transform(payload)
            if not isinstance(transformed, dict):
                raise TypeError(f"{engine.__class__.__name__} transform() must return a dictionary")
            with lock:
                self._queue.push_back(transformed)
            return transformed

        with ThreadPoolExecutor(max_workers=len(self._engines)) as executor:
            for future in [executor.submit(_run, engine) for engine in self._engines]:
                results.append(future.result())

        return results[-1] if results else dict(payload)


__all__ = ["Engine", "Engines", "SampleEngine"]
