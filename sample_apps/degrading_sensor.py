"""Emit successes until a random stop time, then emit failures forever."""

import logging
import random
import time


LOGGER = logging.getLogger("degrading_sensor")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - APPLICATION1 - %(message)s",
    )


def main() -> None:
    configure_logging()
    stop_time = time.monotonic() + random.randint(60, 180)

    while True:
        time.sleep(random.uniform(1, 3))
        if time.monotonic() < stop_time:
            LOGGER.info("Success")
        else:
            LOGGER.info("Failure")


if __name__ == "__main__":
    main()