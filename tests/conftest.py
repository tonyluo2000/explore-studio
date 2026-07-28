"""Shared test fixtures and configuration for engine tests.

Sets SDL_VIDEODRIVER=dummy so Pygame tests run headless.
"""

from __future__ import annotations

import os


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    """Set Pygame to headless mode before any test runs."""
    if "SDL_VIDEODRIVER" not in os.environ:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
