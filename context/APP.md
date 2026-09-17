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