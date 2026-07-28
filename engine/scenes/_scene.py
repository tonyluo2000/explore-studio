"""Explore Studio engine — scene lifecycle.

Defines the Scene base class and lifecycle states. A scene owns the
content of a frame — the application owns execution, the renderer owns
presentation, and the scene owns scene-specific participation.

Scene frame participation is split into two phases:

* **update** — movement, proximity, interaction evaluation (before clear).
* **render** — content drawing (between clear and present).

Internal module — not part of the Student API.
"""

from __future__ import annotations

import enum
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.input import DirectionalInput, InteractionInput

_LOGGER = logging.getLogger("explore-studio.scene")


class SceneState(enum.Enum):
    """Lifecycle states for a scene."""

    CREATED = "created"
    ACTIVE = "active"
    EXITED = "exited"


class SceneLifecycleError(RuntimeError):
    """Raised when an invalid scene lifecycle transition is attempted."""


class Scene:
    """Abstract base for an engine scene.

    Lifecycle::

        Scene()           → CREATED
        scene.enter()     → ACTIVE
        scene.on_frame()  ← called each frame (only in ACTIVE)
        scene.exit()      → EXITED

    Invalid transitions raise SceneLifecycleError:
        - enter() when ACTIVE or EXITED
        - on_frame() when not ACTIVE
        - exit() on CREATED (guarded: logs warning, transitions to EXITED)

    Subclasses override ``on_frame`` to contribute content.
    """

    def __init__(self) -> None:
        self._state = SceneState.CREATED

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> SceneState:
        """Current scene lifecycle state."""
        return self._state

    @property
    def is_active(self) -> bool:
        """True when the scene can participate in frames."""
        return self._state == SceneState.ACTIVE

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def enter(self) -> None:
        """Enter the scene.

        Transitions CREATED → ACTIVE. Called once after the platform
        is initialized and before the first frame.

        Raises:
            SceneLifecycleError: If already ACTIVE or EXITED.
        """
        if self._state == SceneState.ACTIVE:
            raise SceneLifecycleError("Scene is already active.")
        if self._state == SceneState.EXITED:
            raise SceneLifecycleError("Cannot enter a scene that has been exited.")

        self._state = SceneState.ACTIVE
        _LOGGER.debug("Scene entered: %s", type(self).__name__)

    def exit(self) -> None:
        """Exit the scene.

        Transitions ACTIVE → EXITED. Called once during shutdown.
        Idempotent — safe to call on an already-exited scene.

        If called from CREATED, logs a warning and transitions to EXITED
        (handles the case where enter failed before reaching ACTIVE).
        """
        if self._state == SceneState.EXITED:
            return
        if self._state == SceneState.CREATED:
            _LOGGER.warning("Exiting scene that was never entered: %s", type(self).__name__)

        self._state = SceneState.EXITED
        _LOGGER.debug("Scene exited: %s", type(self).__name__)

    # ------------------------------------------------------------------
    # Frame participation
    # ------------------------------------------------------------------

    def update(
        self,
        input_state: DirectionalInput,
        interaction_input: InteractionInput,
        dt: float,
    ) -> None:
        """Update scene state for one frame.

        Called **before** the frame is cleared.  Owns movement,
        proximity, and interaction evaluation.  Must not draw or
        clear anything.

        The default implementation is a no-op — subclasses override
        to contribute update logic.

        Args:
            input_state: Current directional input snapshot.
            interaction_input: Current interaction input snapshot.
            dt: Elapsed time in seconds since the last frame.

        Raises:
            SceneLifecycleError: If the scene is not ACTIVE.
        """
        if self._state != SceneState.ACTIVE:
            raise SceneLifecycleError(f"Cannot update: scene is {self._state.value}.")

    def render(self) -> None:
        """Draw scene content for one frame.

        Called **between** frame clear and frame presentation.  Must
        not update movement, recalculate proximity, evaluate interaction,
        clear the frame, or present the frame.

        The default implementation is a no-op — subclasses override
        to contribute drawing.

        Raises:
            SceneLifecycleError: If the scene is not ACTIVE.
        """
        if self._state != SceneState.ACTIVE:
            raise SceneLifecycleError(f"Cannot render: scene is {self._state.value}.")

    def on_frame(self, input_state: DirectionalInput, dt: float) -> None:
        """Participate in one frame (backward-compatible).

        Delegates to ``update`` (with a default ``InteractionInput``)
        followed by ``render``.  Prefer calling ``update`` and ``render``
        separately in new code.

        Args:
            input_state: Current directional input snapshot.
            dt: Elapsed time in seconds since the last frame.

        Raises:
            SceneLifecycleError: If the scene is not ACTIVE.
        """
        # Import here to avoid circular dependency at module level.
        from engine.input import InteractionInput  # noqa: PLC0415

        self.update(input_state, InteractionInput(), dt)
        self.render()
