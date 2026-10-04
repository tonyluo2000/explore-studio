"""Shared test fixtures and configuration for engine tests.

Sets SDL_VIDEODRIVER=dummy and SDL_AUDIODRIVER=dummy so Pygame tests run
headless and never play sound through the machine's speakers.
"""

from __future__ import annotations

import os


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    """Set Pygame to headless mode before any test runs."""
    if "SDL_VIDEODRIVER" not in os.environ:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    if "SDL_AUDIODRIVER" not in os.environ:
        os.environ["SDL_AUDIODRIVER"] = "dummy"
