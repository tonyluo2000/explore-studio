"""Verify engine logging initialization."""

from __future__ import annotations

import logging

from engine._logging import get_logger, init_logging


def test_init_logging_returns_logger() -> None:
    """init_logging returns a configured Logger instance."""
    logger = init_logging()

    assert isinstance(logger, logging.Logger)
    assert logger.name == "explore-studio"


def test_init_logging_is_idempotent() -> None:
    """Calling init_logging twice returns the same logger."""
    first = init_logging()
    second = init_logging()

    assert first is second


def test_get_logger_returns_logger() -> None:
    """get_logger returns a logger with the engine namespace."""
    logger = get_logger()

    assert isinstance(logger, logging.Logger)
    assert logger.name == "explore-studio"


def test_logger_emits_records(caplog) -> None:  # type: ignore[no-untyped-def]
    """Logger produces log records at the expected level."""
    logger = init_logging()
    logger.info("test message")

    assert "test message" in caplog.text
