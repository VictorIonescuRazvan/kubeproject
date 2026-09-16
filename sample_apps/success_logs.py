"""Emit a small, fixed number of successful log messages."""

import logging
import random
import time


LOGGER = logging.getLogger("success_logs")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - APPLICATION3 - %(message)s",
    )


def main() -> None:
    configure_logging()

    for message_number in range(1, 4):
        time.sleep(random.uniform(1, 3))
        LOGGER.info("Success message %d", message_number)


if __name__ == "__main__":
    main()