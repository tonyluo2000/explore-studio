"""Explore Studio — Student API World model.

A ``World`` collects student-facing entities and launches the engine
when ``run()`` is called.  The ``explore`` package acts as an adapter:
it translates student configuration into engine objects and then
delegates all behaviour to the existing engine.

Ownership: Student API team.
"""

from __future__ import annotations

from explore._character import _FREEZE_MESSAGE, Character, _validate_name
from explore._error import StudentAPIError
from explore._object import Object


class World:
    """Student-facing container for one Character and one Object.

    In v0.1 a world holds exactly one of each.  Duplicate registration
    raises a friendly error.

    ``run()`` translates student configuration into engine objects and
    launches the engine.  Once running, all configuration is frozen.

    Usage::

        world = World("Treasure Island")
        world.add(explorer)
        world.add(chest)
        chest.when_near("Press E to explore")
        chest.when_interacted("You found a treasure!")
        world.run()
    """

    def __init__(self, name: str) -> None:
        self._name = _validate_name(name, "World")
        self._character: Character | None = None
        self._object: Object | None = None
        self._has_run = False

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f'World(name="{self._name}")'

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The world's display name (appears in the window title bar)."""
        return self._name

    @property
    def character(self) -> Character | None:
        """The registered Character, or ``None``."""
        return self._character

    @property
    def object(self) -> Object | None:
        """The registered Object, or ``None``."""
        return self._object

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add(self, entity: Character | Object) -> None:
        """Register a Character or Object with this world.

        Exactly one Character and one Object are permitted.  Adding a
        second of either type raises ``StudentAPIError``.

        Configuration (e.g. ``chest.when_near(...)``) may be set before
        or after calling ``add()`` — the entity stores its own config.

        Args:
            entity: A ``Character`` or ``Object`` instance.

        Raises:
            StudentAPIError: If a Character or Object is already
                registered, if *entity* is not a recognised type, or
                if the world is already running.
        """
        if self._has_run:
            raise StudentAPIError(_FREEZE_MESSAGE)
        if isinstance(entity, Character):
            if self._character is not None:
                raise StudentAPIError(
                    "This world already has a character.\n"
                    "Student API v0.1 supports one character at a time."
                )
            self._character = entity
        elif isinstance(entity, Object):
            if self._object is not None:
                raise StudentAPIError(
                    "This world already has an object.\n"
                    "Student API v0.1 supports one object at a time."
                )
            self._object = entity
        else:
            raise StudentAPIError(
                "You can only add a Character or an Object to the world.\n"
                f"You gave: {type(entity).__name__}"
            )

    def _remove_registration_entity(self, entity: Character | Object) -> None:
        """Remove an exact entity during registration-transaction rollback.

        This is an internal hook for the explicit package application adapter,
        not part of the student-facing API. Identity checks ensure rollback
        cannot remove pre-existing or replacement state.
        """
        if self._has_run:
            raise StudentAPIError(_FREEZE_MESSAGE)
        if isinstance(entity, Character) and self._character is entity:
            self._character = None
            return
        if isinstance(entity, Object) and self._object is entity:
            self._object = None
            return
        raise StudentAPIError("The registration entity is not owned by this world.")

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Launch the world.

        Translates student configuration into engine objects, constructs
        the engine application, and starts the main loop.  Blocks until
        the window is closed.

        Raises:
            StudentAPIError: If the required character or object has
                not been added, or if ``run()`` has already been called.
        """
        if self._has_run:
            raise StudentAPIError(
                "This world is already running.\n\n" "Create a new World to start again."
            )
        if self._character is None:
            raise StudentAPIError("Add one Character before running the world.")
        if self._object is None:
            raise StudentAPIError("Add one Object before running the world.")

        # --- freeze student configuration ---
        self._has_run = True
        self._character._freeze()
        self._object._freeze()

        # --- translate student objects → engine objects ---
        from engine._config import Config
        from engine._platform import Platform
        from engine.entities import Character as EngineCharacter
        from engine.entities import WorldObject as EngineWorldObject
        from engine.rendering import Renderer
        from engine.scenes._default_scene import DefaultScene

        # Build engine Config from world name.
        config = Config(app_name=self._name)

        # Build engine Character from student Character.
        engine_character = EngineCharacter(
            name=self._character.name,
            x=self._character.x,
            y=self._character.y,
            width=100,
            height=100,
            color=self._character.color_rgb,
        )

        # Build engine WorldObject from student Object.
        engine_object = EngineWorldObject(
            name=self._object.name,
            x=self._object.x,
            y=self._object.y,
            width=80,
            height=60,
            color=self._object.color_rgb,
        )

        # --- construct and launch engine ---
        platform = Platform(config)
        platform.initialize()
        try:
            renderer = Renderer(platform)
            scene = DefaultScene(
                renderer,
                character=engine_character,
                world_object=engine_object,
                near_message=self._object.near_message,
                interacted_message=self._object.interacted_message,
            )
            scene.enter()

            # Main loop (mirrors App._run_loop structure).
            while True:
                frame_events = platform.poll_frame_events()
                if frame_events.quit_requested:
                    break

                dt = platform.tick()
                inp = platform.poll_directional_input()

                from engine.input import InteractionInput

                interaction_input = InteractionInput(
                    interact_pressed=frame_events.interaction_pressed,
                )
                scene.update(inp, interaction_input, dt)
                renderer.clear_frame(config.background_color)
                scene.render()
                renderer.present_frame()

        except Exception as exc:
            raise StudentAPIError("The world ran into a problem and had to close.") from exc
        finally:
            # --- cleanup ---
            import contextlib

            with contextlib.suppress(Exception):
                scene.exit()
            platform.shutdown()
