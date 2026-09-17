import threading

import pytest

from engines import Engine, Engines, SampleEngine


class TrackingQueue:
    def __init__(self):
        self.items = []
        self.lock = threading.Lock()

    def push_back(self, item):
        with self.lock:
            self.items.append(item)


class PassthroughEngine(Engine):
    def transform(self, payload):
        return dict(payload)


def test_engine_requires_queue_with_push_back():
    with pytest.raises(TypeError):
        Engine(queue=None)

    with pytest.raises(TypeError):
        Engine(queue=object())


def test_sample_engine_returns_deep_copy():
    queue = TrackingQueue()
    engine = SampleEngine(queue)
    payload = {"nested": {"value": 1}, "items": [1, 2, 3]}

    result = engine.transform(payload)

    assert result == payload
    assert result is not payload
    assert result["nested"] is not payload["nested"]
    assert result["items"] is not payload["items"]


def test_engines_runs_in_parallel_and_pushes_results():
    queue = TrackingQueue()
    engines = Engines(queue)

    payload = {"value": 1}
    result = engines.transform(payload)

    assert result["value"] == 1
    assert len(queue.items) == 1
    assert queue.items[0]["value"] == 1
