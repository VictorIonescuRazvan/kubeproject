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

# Sample applications
This folder will store some simple python, no dependency applications.

These should output things to stdout as if they were logs.

The following templates should be here:
- a script that outputs "success" log messages, at random intervals. It should have a predefined number of such messages (around 3)
- a script that sometimes outputs "failure", around 1/10 chance
- a script that outputs success until a stop time (chosen randomly, 1-3 minutes after start). Afterwards, only outputs failure

# Logging format
Refer to LOGGING.md at the root of this project or attached as context for context.
