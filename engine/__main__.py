"""Explore Studio engine — command-line entry point.

Usage:
    python -m engine

Initializes configuration, logging, the platform (Pygame + window),
and the application lifecycle. Opens an empty window that can be
closed normally. Exits cleanly on window close.
"""

from __future__ import annotations

from engine.app import App

if __name__ == "__main__":
    App.main()
