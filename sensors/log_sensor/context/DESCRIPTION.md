# Application context
The application is split into multiple components:
- a number of sensors
- an aggregator
- consumers

The implementation details of consumers are not relevant for the below.

The sensor:
- gathers data from the environment (sensor specific)
- authenticates with the aggregator
- publishes data to the aggregator

# Purpose
Send pod logs every x seconds (defined below via INTERVAL).

# Environment
Assume the application will be run inside of a Kubernetes deployment as a pod.

A single file will be mounted, see below.

# Environment variables

The following environment variables are expected
- CONTEXT: path of a file that will specify context to be sent with each log. 
- NAMESPACE: the namespace to monitor
- INTERVAL: interval in seconds at which to send pod logs for a specific pod

# Data format
- the data is JSON
- it has the following primitive:
{
	"pod": <pod name as string>
	"namespace": <name of the namespace>
	"data": <the log text>
	"context": <additional context string>
}

# Implementation details
Maintain an internal pod structure. If a pod goes offline, print last set of logs and remove from internal structure. Iterate the structure every INTERVAL seconds.

Use Kubernetes Python Client for this.

For connecting to the aggregator, use the connector provided as context. Import it as editable lib.

# Logging
See LOGGING.md, in the tree of the project or attached as context. The application should log:
- initialization failures -> invalid environment variables, issues with acquiring a connection via the connector
- message size before sending, 
