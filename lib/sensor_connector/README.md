# sensor_connector

`sensor_connector` is a small HTTP client for sensors that authenticate with an
aggregator and publish sensor data to it.

## API

### `connect(api_key, context, hostname)`

Authenticates the sensor with the aggregator. The connector sends the API key
using Basic Auth and persists the returned token for subsequent calls.

- `api_key`: credentials supplied by the aggregator.
- `context`: additional information about the sensor or its data. When the
	aggregator endpoint is AI-based, this string provides context that can help
	the AI interpret or process the published data.
- `hostname`: the aggregator base URL, such as `https://aggregator.example`.

The method returns the authentication token issued by the aggregator.

### `publish(data)`

Publishes a dictionary of sensor data to the aggregator using the token returned
by `connect`. If the token is rejected with HTTP 401, the connector reconnects
using the previously supplied credentials and context, then retries the
publication once.

```python
from sensor_connector import SensorConnector

connector = SensorConnector()
connector.connect(
		api_key="sensor-api-key",
		context="This sensor measures temperature in a refrigerated warehouse.",
		hostname="https://aggregator.example",
)
connector.publish({"temperature_celsius": 4.2})
```
