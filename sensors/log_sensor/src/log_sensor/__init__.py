"""Kubernetes pod log sensor."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Protocol

from kubernetes import client, config
from sensor_connector import SensorConnector


LOGGER = logging.getLogger("log_sensor")
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - log_sensor - %(message)s")
    )
    LOGGER.addHandler(handler)
LOGGER.propagate = False


class Connector(Protocol):
    def connect(self, api_key: str, context: str, hostname: str) -> str: ...

    def publish(self, data: dict[str, str]) -> None: ...


@dataclass(frozen=True)
class Settings:
    context_path: str
    namespace: str
    interval: float
    api_key: str
    aggregator: str

    @classmethod
    def from_environment(cls) -> "Settings":
        context_path = _required_environment("CONTEXT")
        namespace = _required_environment("NAMESPACE")
        api_key = _required_environment("API_KEY")
        aggregator = _required_environment("AGGREGATOR_HOSTNAME")
        interval_text = _required_environment("INTERVAL")
        try:
            interval = float(interval_text)
        except ValueError as error:
            raise ValueError("INTERVAL must be a number") from error
        if interval <= 0:
            raise ValueError("INTERVAL must be greater than zero")
        return cls(context_path, namespace, interval, api_key, aggregator)


@dataclass
class PodState:
    name: str
    logs: str = ""


class LogSensor:
    """Collect and publish logs for pods in one Kubernetes namespace."""

    def __init__(
        self,
        settings: Settings,
        connector: Connector,
        core_api: Any,
        context: str,
    ) -> None:
        self.settings = settings
        self.connector = connector
        self.core_api = core_api
        self.context = context
        self.pods: dict[str, PodState] = {}

    @classmethod
    def create(cls) -> "LogSensor":
        settings = Settings.from_environment()
        try:
            with open(settings.context_path, encoding="utf-8") as context_file:
                context = context_file.read()
        except OSError as error:
            raise ValueError(f"Unable to read CONTEXT file: {error}") from error

        try:
            config.load_incluster_config()
            core_api = client.CoreV1Api()
        except Exception as error:
            raise RuntimeError(f"Unable to initialize Kubernetes client: {error}") from error

        connector = SensorConnector()
        try:
            connector.connect(settings.api_key, context, settings.aggregator)
        except Exception as error:
            raise RuntimeError(f"Unable to connect to aggregator: {error}") from error
        return cls(settings, connector, core_api, context)

    def run(self) -> None:
        while True:
            self.iterate()
            time.sleep(self.settings.interval)

    def iterate(self) -> None:
        response = self.core_api.list_namespaced_pod(self.settings.namespace)
        current_names = {pod.metadata.name for pod in response.items if pod.metadata.name}

        for name in sorted(set(self.pods) - current_names):
            state = self.pods.pop(name)
            self._publish(name, state.logs)

        for name in sorted(current_names):
            state = self.pods.setdefault(name, PodState(name))
            state.logs = self.core_api.read_namespaced_pod_log(
                name=name,
                namespace=self.settings.namespace,
            )
            self._publish(name, state.logs)

    def _publish(self, pod_name: str, logs: str) -> None:
        payload = {
            "pod": pod_name,
            "namespace": self.settings.namespace,
            "data": logs,
            "context": self.context,
        }
        message_size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        LOGGER.info("Sending message for pod %s (%d bytes)", pod_name, message_size)
        self.connector.publish(payload)


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def main() -> None:
    try:
        LogSensor.create().run()
    except (OSError, RuntimeError, ValueError) as error:
        LOGGER.info("Initialization failed: %s", error)
        raise SystemExit(1) from error
