# Aggregator

This service accepts sensor data, validates credentials, transforms payloads through the configured engine, and forwards the processed messages to a destination broker.

## Exposed endpoints

### POST /connect
Authenticates a sensor using an API key sent in the Basic Authorization header.

Request example:

```http
POST /connect
Authorization: Basic <base64(api_key)>
Content-Type: application/json
```

Body:

```json
{
  "uuid": "sensor-uuid",
  "context": "sensor-context"
}
```

Response:

```json
{
  "token": "<issued-token>"
}
```

Returns `401` when the API key is invalid.

### POST /publish
Accepts sensor payloads and validates the supplied token in the Basic Authorization header.

Request example:

```http
POST /publish
Authorization: Basic <base64(token)>
Content-Type: application/json
```

Body:

```json
{
  "sensor": "demo",
  "value": 42
}
```

Response:

```json
{
  "status": "accepted"
}
```

Returns `202 Accepted` when the payload has been accepted for processing and queueing. Returns `401` when the token is invalid.

## Logging expectations

The app logs at INFO level to stdout using the format:

```text
%(asctime)s - %(levelname)s - Aggregator - %(message)s
```

Expected logging includes:
- incoming requests and the endpoint they hit
- request payloads when `CONNECTION_LOGS` is enabled
- Authorization headers are redacted before logging
- queue pop events and engine processing events
- broker send start and response receipt
- full broker payload logging only when `CONNECTION_LOGS` is enabled
