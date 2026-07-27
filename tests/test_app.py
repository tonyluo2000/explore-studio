"""Verify application bootstrap behavior."""

from __future__ import annotations

from engine import App, Config
from engine._logging import init_logging


def test_app_creation() -> None:
    """App can be created with default config."""
    app = App()
    assert app.config.app_name == "Explore Studio"


def test_app_creation_custom_config() -> None:
    """App accepts a custom Config."""
    config = Config(app_name="Custom")
    app = App(config=config)
    assert app.config.app_name == "Custom"


def test_app_start_shutdown_sequence() -> None:
    """App can start and shut down without error."""
    # Ensure logging is initialized before App.start in test context.
    init_logging()

    app = App()
    app.start()
    app.shutdown()


def test_app_double_start_raises() -> None:
    """Starting the app twice raises RuntimeError."""
    import pytest

    init_logging()

    app = App()
    app.start()

    with pytest.raises(RuntimeError, match="already been called"):
        app.start()
