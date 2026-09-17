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

# Individual engines
Engines are tasked with transforming data and publishing them on a queue. This is the `Engine` template for an individual engine type.

The constructor takes a queue. The queue object should expose a push_back method taking one argument (not necessarily a dictionary, just check that it exists and is callable).

The engine exposes a single `transform` method that takes a dictionary as input and returns a dictionary. Assume that the input dictionary is const - try to find a pattern that enforces / strongly indicates this. Don't worry about mutable members - we can't control them.

Create a template for this so other objects can inherit.

Implement a sample engine that returns a deep copy of the same dictionary.

# Engines
The Engines module is tasked with managing the different engines imported by the aggregator.

The Engines module assumes that all engines conform to the Engine template defined above.

The Engines will have a similar constructor, see above.

The exposed method is the same `transform`, but calls all engines on it.

Engines should be run in parallel. Assume read-only on the dictionary accross engines - find the appropriate synchronisation primitive. Assume that the queue is NOT thread safe.

Logging is managed by the individual engines. Only log which engines are loaded - module names.