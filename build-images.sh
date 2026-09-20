#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

printf '\n==> Building aggregator image: aggregator:latest\n'
docker build -t aggregator:latest -f aggregator/Dockerfile .

printf '\n==> Building log sensor image: log-sensor:latest\n'
docker build -t log-sensor:latest -f sensors/log_sensor/Dockerfile .

printf '\n==> Building InfluxDB connector image: influxdb-connector:latest\n'
docker build -t influxdb-connector:latest -f adapters/InfluxDB_connector/Dockerfile .

printf '\n==> Building sample app images\n'
docker build -t degrading-sensor:latest -f sample_apps/degrading_sensor.Dockerfile .
docker build -t intermittent-failures:latest -f sample_apps/intermittent_failures.Dockerfile .
docker build -t success-logs:latest -f sample_apps/success_logs.Dockerfile .

printf '\n==> Loading images into kind cluster: monitoring\n'
kind load docker-image \
	aggregator:latest \
	log-sensor:latest \
	 influxdb-connector:latest \
	degrading-sensor:latest \
	intermittent-failures:latest \
	success-logs:latest \
	--name monitoring

printf '\n==> Reapplying manifests\n'
kubectl apply -f manifests

printf '\n==> Restarting monitoring containers\n'
kubectl rollout restart deployments --namespace monitoring

printf '\n==> Done\n'
