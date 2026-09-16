# Logging

This file describes the logging format and general guidelines.

## Library
For python, use `logging`. The logging should always be at INFO level, logging everything.

Generally, expect that each python module will log to stdout.

## Format
Format is as follows:
format="%(asctime)s - %(levelname)s - <MODULE> - %(message)s"

`MODULE` is hardcoded in each module. An example is:
2026-09-16 20:53:12,123 - INFO - Connector - Application started

