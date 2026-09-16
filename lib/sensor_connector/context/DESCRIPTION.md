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

# Description

This is a dependency module that will be loaded by any sensor. It will be a class that exposes two methods:

- `connect`: the purpose of this method is to send an authentication to the aggregator and handle the response
- `publish`: the puspose of this method is to send data to the aggregator and handle the response

## Connnect
This section describes the implementation of the `connect` method.

### Interface
The `connect` receives the following:
- an apikey
- a context string, used by the sensor to provide AI context to the aggregator
- a hostname or ip (general destination) where the aggregator is placed

### Endpoint
The connection is POST. The endpoint expects a JSON with the following format:
{
	'uuid': <uuid4 string>
	'context': <context string>
}
The apikey is transmited via Basic Auth header.


### Flow
The expected results are:
- 200 with a token in the body. The body is a json in the following format: {'token':<token>}. The token is a string.
- 400 bad request - throw generic exception
- 401 auth - throw exception detailing invalid credentials
- 500 - throw exception detailing server side error

### Persistence
Persist the token. This should be an internal attribute.
Persist the last address connected to. Persist the API key.

## Publish
This section describes the implementation of the `publish` method.

### Interface
The `publish` method receives the following:
- a dictionary

### Endpoint
The connection is POST. The endpoint expects a JSON. This is the dictionary passed as an argument.
The token is transmited via Basic Auth header.

### Flow
1. send the request
2. on 401, use connect to reconnect. On failure, throw and exit
3. resend the request. On failure, throw and exit

The expected results are:
- 202 - all is well
- 400 - throw exception with response body
- 401 - authentication issue, refer to flow above
- 500 - throw exception detailing server side error

## Logging
The module will be called `sensor_connector` in logs. It will log the following information:
- each request: 1. what it attempts (e.g. Connecting to hostname. or Submitting data to hostname) 2. what it receives (e.g. Successfully sent data. or Failed with <error> and <message>)
