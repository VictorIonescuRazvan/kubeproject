# Application context
The application is split into multiple components:
- a number of sensors
- an aggregator
- consumers

## Sensors

Sensors are standalone Dockerized applications that gather data from their surroundings.

For example, a sensor could pull log information from kube pods in a certain namespace.

The sensor publishes that data to an aggregator.

The sensor forms a session with the aggregator, obtaining a token. The sensor is identified by an uuid, which it controls (sends when registering).

## Aggregator

The aggregator receives data, applies processing, queues the resulting messages and publishes them to a message queue.

The aggregator exposes two endpoints:
- auth -> generates a token on valid API key
- publish -> receives data from sensors

The aggregator's logic is split in the following steps:
- listens to data
- authenticates the message. If the token is valid, forwards it to engines
- engines apply a transformation (or none) on the message
- engines queue the resulting messages on a timestamp-based priority queue
- queue publishes the information to a message broker

## Consumers

Not implemented in here. They receive data via a message broker from the aggregator. The aggregator is not aware of individual consumers. There is no confirmation that the data is received, and the aggregator performs no retransmission based on consumer availability. This does not exclude retransmission to the message broker.


# Aggregator
This is the aggregator application. This applicaiton exposes two POST endpoints:
- an `auth` endpoint for authenticating
- a `submit` endpoint for submitting data

This should be a FastAPI app.

## Modules
Use the following libraries in the lib folder (attached as context):
- `auth` - for managing authentication and valid tokens
- `engines` - for loading engines and processing data
- `queue` - for queueing data processed by engines

## Authentication
Authentication is performed via the `auth` endpoint. The purpose of this endpoint is to validate the API key sent by a sensor and to generate a token.

Expose this functionality via the `auth` POST endpoint.

## Data ingestion
The flow is the following:
1. a request is received, data included, via header. See snippet from connector code:
```python
        request = Request(
            address,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Basic "
                + base64.b64encode(credential.encode("utf-8")).decode("ascii"),
                "Content-Type": "application/json",
            },
            method="POST",
        )
```
2. if authentication is valid, the engines are via the exposed API.
3. the engines are provided a Queue object on initialisation
4. data is popped from the queue. Sending data to the consumer is synchronized - the application waits for it to be received by the eventual data broker with a timeout of 5 seconds. This is handled by a sepparate thread that checks the queue for items continously, with a 5 second backoff if queue is empty.

The address and port of the message broker are indicated by the enviornment variables DESTINATION_IP and DESTINATION_PORT.

## Logging
All requests received - authentication and data, is logged. The full request (API / bearer token censored) is logged if an environment variable called "CONNECTION_LOGS" is set.

The action of popping the queue is logged. Each call to the engines is logged.

Sending data to the message broker is logged when starting the send and when receiving the response. Full data sent to the broker is logged if the environment variable "CONNECTION_LOGS" is set.