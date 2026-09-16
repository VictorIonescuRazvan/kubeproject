## Configuration

The sensor expects these environment variables:

- `CONTEXT`: path to the context file sent with every message
- `NAMESPACE`: Kubernetes namespace to monitor
- `INTERVAL`: polling interval in seconds
- `API_KEY`: aggregator API key
- `AGGREGATOR_HOSTNAME`: aggregator base URL

Run it with `log-sensor` inside a Kubernetes pod using an in-cluster service account
that can list pods and read pod logs.
