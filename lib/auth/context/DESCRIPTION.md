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

# Auth
This module is tasked with:
- checking an API key against a preconfigured value
- emitting an unique token on successful authentication
- expiring the token after a certain time

## API key
The API key is specified in an environment variable.

## Tokens
Tokens are uuid7 strings. They are stored in an associative map token -> expiry datetime. Expiration is defined as an environment variable, and is 5 minutes by default.

The application keeps a priority queue in paralel of expiry -> token, earliest datetime at the front. On adding a token, the queue head is evaluated and if expired popped. The entry is deleted from the map on expiry.

In total you have two structures:
- associative map token -> datetime
- priority queue datetime -> token

## Exposed functions
This class will expose two methods:
- get_token
    - takes an api key as an argument
    - returns None on invalid api key
    - returns the token on valid api key
    - follows the token management plan above
- auth
    - takes a token as an argument
    - returns false on invalid token 
    - returns true on valid token

## Logging
Follow LOGGING.md at the root/context of this project, or attached as context.

The logging should happen at the beggining and the end of get_token and auth. Logging should not expose api key or token.