## InfluxDB connector

The connector accepts a `POST` containing JSON with string fields `pod`, `namespace`, and `data`. It converts the payload to InfluxDB line protocol and writes it to `/api/v2/write` using the configured InfluxDB token.

The HTTP listener uses `HOST` (default `0.0.0.0`) and `PORT` (default `8000`). InfluxDB is configured with `INFLUXDB_HOST` (default `localhost`), `INFLUXDB_PORT` (default `8086`), `INFLUXDB_ORG` (default `default-org`), `INFLUXDB_BUCKET` (default `default-bucket`), `INFLUXDB_TOKEN` (default `influxdb-connector-token`), and `INFLUXDB_MEASUREMENT` (default `logs`).

Example request:

```json
{"pod":"api-0","namespace":"production","data":"request completed"}
```
