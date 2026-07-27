"""Explore Studio engine — centralized logging.

Provides a single logger namespace for the entire engine. All subsystems
log through this module rather than configuring their own loggers.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
import sys

_LOGGER_NAME = "explore-studio"
_logger: logging.Logger | None = None


def init_logging(*, level: int = logging.DEBUG) -> logging.Logger:
    """Initialize centralized engine logging.

    Configures console output with a human-readable format suitable for
    development debugging. Idempotent — subsequent calls return the
    existing logger without reconfiguring.

    Args:
        level: Logging level (default: DEBUG for development).

    Returns:
        The configured engine-wide logger.
    """
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Return the engine-wide logger.

    Returns:
        The configured logger, or a default logger if init_logging has
        not been called.
    """
    if _logger is not None:
        return _logger
    return logging.getLogger(_LOGGER_NAME)
