"""Emit success logs with an occasional failure."""

import logging
import random
import time


LOGGER = logging.getLogger("intermittent_failures")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - APPLICATION2 - %(message)s",
    )


def main() -> None:
    configure_logging()

    while True:
        time.sleep(random.uniform(1, 3))
        if random.randrange(10) == 0:
            LOGGER.critical("Failure")
        else:
            LOGGER.info("Success")


if __name__ == "__main__":
    main()