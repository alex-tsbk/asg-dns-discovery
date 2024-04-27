import logging
import os
from functools import cache

from app.context import RUNTIME_CONTEXT

if RUNTIME_CONTEXT.is_aws:
    # Reduce boto3 logging noise for third-party libraries
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    logging.getLogger("nose").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)

# Environment variables
LOG_LEVEL = os.environ.get("log_level", "DEBUG").upper()
LOG_IDENTIFIER = os.environ.get("log_identifier", "sg-dns-discovery")


@cache
def get_logger() -> logging.Logger:
    """Returns instance of logging.Logger class any consumer requiring logger"""
    return _build_application_logger()


def _build_application_logger() -> logging.Logger:
    """Returns instance of logging.Logger class"""
    logger = logging.getLogger(LOG_IDENTIFIER)
    logger.propagate = False  # Prevents duplicate logs

    # Set logging level based on configuration environment variable
    numeric_level = getattr(logging, LOG_LEVEL, None)
    if not isinstance(numeric_level, int):
        # Fall back to INFO level by default
        numeric_level = logging.INFO
    logger.setLevel(numeric_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(thread)d:%(levelname)s:%(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
