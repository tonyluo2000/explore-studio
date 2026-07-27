"""Explore Studio engine — command-line entry point.

Usage:
    python -m engine

Initializes configuration, logging, and the application lifecycle,
then exits cleanly. At this milestone no window is opened.
"""

from __future__ import annotations

from engine import App, Config


def main() -> None:
    """Application entry point."""
    config = Config()
    app = App(config=config)

    try:
        app.start()
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
