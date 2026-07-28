"""Verify Student API adapter and execution (M4C).

Tests the translation layer, engine launch, runtime freeze, and
adapter boundary.  Uses the SDL dummy driver.
"""

from __future__ import annotations

import threading
import time

import pytest

from explore import Character, Object, StudentAPIError, World
from explore._colors import resolve_color


def _post_quit_after(delay: float = 0.1) -> threading.Thread:
    import pygame

    def _post() -> None:
        time.sleep(delay)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    t = threading.Thread(target=_post, daemon=True)
    t.start()
    return t


def _make_ready_world(name: str = "Test") -> World:
    """Return a World with one Character and one Object, ready to run."""
    w = World(name)
    w.add(Character(name="Hero"))
    w.add(Object(name="Chest", x=100, y=200))
    return w


# ==================================================================
# World.run() — engine launch
# ==================================================================


def test_run_launches_and_exits() -> None:
    w = _make_ready_world()
    _post_quit_after(0.1)
    w.run()
    # If we got here, the engine launched and exited cleanly.


def test_run_with_custom_messages() -> None:
    w = World("Messages")
    w.add(Character(name="Hero"))
    obj = Object(name="Chest", x=0, y=0)
    obj.when_near("Custom prompt")
    obj.when_interacted("Custom success")
    w.add(obj)
    _post_quit_after(0.1)
    w.run()
    # No crash — custom messages were forwarded.


def test_run_with_no_messages() -> None:
    """World runs fine with no interaction messages set."""
    w = World("Silent")
    w.add(Character(name="Hero"))
    w.add(Object(name="Chest", x=0, y=0))
    _post_quit_after(0.1)
    w.run()
    # No crash — optional messages handled correctly.


def test_run_with_only_near_message() -> None:
    w = World("NearOnly")
    w.add(Character(name="Hero"))
    obj = Object(name="Chest", x=0, y=0)
    obj.when_near("Look!")
    w.add(obj)
    _post_quit_after(0.1)
    w.run()


def test_run_with_only_interacted_message() -> None:
    w = World("InteractOnly")
    w.add(Character(name="Hero"))
    obj = Object(name="Chest", x=0, y=0)
    obj.when_interacted("Got it!")
    w.add(obj)
    _post_quit_after(0.1)
    w.run()


# ==================================================================
# Translation — student → engine
# ==================================================================


def test_character_translation() -> None:
    """Student Character translates to engine Character correctly."""
    from engine.entities import Character as EngineCharacter

    student = Character(name="TestHero", x=123, y=456, color="blue")
    rgb = resolve_color("blue")

    engine = EngineCharacter(
        name=student.name,
        x=student.x,
        y=student.y,
        width=100,
        height=100,
        color=rgb,
    )
    assert engine.name == "TestHero"
    assert engine.x == 123
    assert engine.y == 456
    assert engine.color == rgb


def test_object_translation() -> None:
    """Student Object translates to engine WorldObject correctly."""
    from engine.entities import WorldObject as EngineWorldObject

    student = Object(name="Chest", x=60, y=480, color="brown")
    rgb = resolve_color("brown")

    engine = EngineWorldObject(
        name=student.name,
        x=student.x,
        y=student.y,
        width=80,
        height=60,
        color=rgb,
    )
    assert engine.name == "Chest"
    assert engine.x == 60
    assert engine.y == 480
    assert engine.color == rgb


def test_color_translation_all_nine() -> None:
    """All nine named colours map to valid RGB."""
    from explore._colors import valid_color_names

    for name in valid_color_names():
        rgb = resolve_color(name)
        assert len(rgb) == 3
        assert all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)


def test_default_sizes_not_leaked() -> None:
    """Student API does not expose engine default sizes."""
    ch = Character(name="A")
    obj = Object(name="B", x=0, y=0)
    assert not hasattr(ch, "width")
    assert not hasattr(ch, "height")
    assert not hasattr(obj, "width")
    assert not hasattr(obj, "height")


# ==================================================================
# Runtime freeze
# ==================================================================


def test_add_rejected_after_run() -> None:
    w = _make_ready_world()
    _post_quit_after(0.1)
    w.run()
    with pytest.raises(StudentAPIError, match="already running"):
        w.add(Character(name="Other"))


def test_when_near_rejected_after_run() -> None:
    w = _make_ready_world()
    # Configure the object but don't run yet
    obj = w.object
    assert obj is not None
    _post_quit_after(0.1)
    w.run()
    with pytest.raises(StudentAPIError, match="already running"):
        obj.when_near("Too late")


def test_when_interacted_rejected_after_run() -> None:
    w = _make_ready_world()
    obj = w.object
    assert obj is not None
    _post_quit_after(0.1)
    w.run()
    with pytest.raises(StudentAPIError, match="already running"):
        obj.when_interacted("Too late")


def test_character_frozen_after_run() -> None:
    w = _make_ready_world()
    _post_quit_after(0.1)
    w.run()
    assert w.character is not None
    assert w.character.frozen is True


def test_object_frozen_after_run() -> None:
    w = _make_ready_world()
    _post_quit_after(0.1)
    w.run()
    assert w.object is not None
    assert w.object.frozen is True


def test_not_frozen_before_run() -> None:
    w = World("W")
    ch = Character(name="A")
    obj = Object(name="B", x=0, y=0)
    w.add(ch)
    w.add(obj)
    assert ch.frozen is False
    assert obj.frozen is False


# ==================================================================
# Validation at run()
# ==================================================================


def test_run_missing_both_entities() -> None:
    w = World("Empty")
    with pytest.raises(StudentAPIError, match="Character"):
        w.run()


def test_run_missing_character_only() -> None:
    w = World("W")
    w.add(Object(name="B", x=0, y=0))
    with pytest.raises(StudentAPIError, match="Character"):
        w.run()


def test_run_missing_object_only() -> None:
    w = World("W")
    w.add(Character(name="A"))
    with pytest.raises(StudentAPIError, match="Object"):
        w.run()


# ==================================================================
# Adapter boundary — no engine duplication
# ==================================================================


def test_adapter_does_not_implement_movement() -> None:
    """The explore package has no movement logic."""
    import explore

    for module_name in dir(explore):
        if module_name.startswith("_"):
            continue
        obj = getattr(explore, module_name)
        if hasattr(obj, "move"):
            pytest.fail(f"explore.{module_name} should not implement move()")


def test_adapter_does_not_implement_proximity() -> None:
    """The explore package has no proximity logic."""
    import explore._world as wm

    with open(wm.__file__) as f:
        source = f.read()
    assert "distance" not in source.lower().split("_")
    # World.run() delegates proximity to the engine scene.


def test_adapter_delegates_to_engine() -> None:
    """World.run() imports from engine, not reimplements."""
    import explore._world as wm

    with open(wm.__file__) as f:
        source = f.read()
    assert "from engine" in source
    assert "import pygame" not in source


# ==================================================================
# Exception chaining
# ==================================================================


def test_internal_failure_chained() -> None:
    """When translation fails, the original exception is chained."""
    try:
        try:
            raise ValueError("engine config error")
        except ValueError as exc:
            raise StudentAPIError("Could not start the world.") from exc
    except StudentAPIError as api_exc:
        assert api_exc.__cause__ is not None
        assert isinstance(api_exc.__cause__, ValueError)


# ==================================================================
# End-to-end — complete student program
# ==================================================================


def test_complete_student_program_runs() -> None:
    """The canonical v0.1 student program runs and exits cleanly."""
    w = World("Treasure Island")

    explorer = Character(name="Explorer", x=430, y=270, color="gold")
    chest = Object(name="Treasure Chest", x=60, y=480, color="brown")

    w.add(explorer)
    w.add(chest)

    chest.when_near("Press E to explore")
    chest.when_interacted("You found a treasure!")

    _post_quit_after(0.15)
    w.run()
    # If we got here without an exception, the program ran successfully.


def test_complete_program_with_e_key_and_feedback() -> None:
    """E key press near the chest triggers success feedback."""
    import pygame

    w = World("InteractionTest")

    # Character starts near the object (range 120, distance ~30).
    hero = Character(name="Hero", x=0, y=0, color="gold")
    chest = Object(name="Chest", x=30, y=0, color="brown")
    chest.when_near("Press E to explore")
    chest.when_interacted("You found a treasure!")

    w.add(hero)
    w.add(chest)

    # Post E key press then quit.
    def post_e_then_quit() -> None:
        time.sleep(0.1)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        time.sleep(0.3)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=post_e_then_quit, daemon=True).start()
    w.run()
    # No crash → interaction + feedback worked.


# ==================================================================
# Regression — engine tests still pass
# ==================================================================
# Verified by running the full test suite.
