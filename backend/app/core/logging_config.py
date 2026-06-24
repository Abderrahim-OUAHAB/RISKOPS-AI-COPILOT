import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    level_name = settings.log_level.upper().strip()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    for noisy_logger in ["httpx", "urllib3", "watchfiles"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
