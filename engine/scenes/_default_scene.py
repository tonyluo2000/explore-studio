"""Explore Studio engine — default empty scene.

A minimal scene with no gameplay, no objects, no assets, and no input
processing. Exists solely to demonstrate the scene lifecycle contract.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from engine.scenes._scene import Scene


class DefaultScene(Scene):
    """An intentionally empty default scene.

    Enters, participates in frames (as a no-op), and exits cleanly.
    Used when the application needs a scene but no specific content
    has been configured.
    """

    def on_frame(self) -> None:
        """No-op: this scene contributes no content to frames."""
        super().on_frame()
