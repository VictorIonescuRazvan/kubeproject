"""Sample engine implementation."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from .engine import Engine


class SampleEngine(Engine):
    """Return a deep copy of the input payload."""

    def transform(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return copy.deepcopy(dict(payload))


__all__ = ["SampleEngine"]
