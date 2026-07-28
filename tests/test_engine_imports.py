"""Verify all engine packages are importable."""

from __future__ import annotations


def test_engine_package_imports() -> None:
    """The top-level engine package imports without error."""
    import engine  # noqa: F401


def test_engine_subsystem_imports() -> None:
    """All engine subsystems are importable packages."""
    from engine import (  # noqa: F401
        animation,
        assets,
        audio,
        dialogue,
        entities,
        interactions,
        persistence,
        rendering,
        scenes,
        ui,
        world,
    )


def test_public_api_exports() -> None:
    """Engine __init__ exports the expected public symbols."""
    from engine import App, Config, LifecycleError, init_logging  # noqa: F401


def test_platform_module_importable() -> None:
    """The internal platform module is importable."""
    from engine import _platform  # noqa: F401
