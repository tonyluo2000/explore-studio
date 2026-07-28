"""Verify Student API model foundation (M4B).

Tests the ``explore`` package: World, Character, Object, named colours,
validation, cardinality, and deferred run().  No engine is launched.
"""

from __future__ import annotations

import pytest

from explore import Character, Object, StudentAPIError, World
from explore._colors import resolve_color, valid_color_names

# ==================================================================
# Named colours
# ==================================================================


def test_all_nine_colors_accepted() -> None:
    names = valid_color_names()
    assert len(names) == 9
    assert names == [
        "blue",
        "brown",
        "gold",
        "green",
        "orange",
        "pink",
        "purple",
        "red",
        "yellow",
    ]


def test_each_color_resolves_to_rgb() -> None:
    for name in valid_color_names():
        rgb = resolve_color(name)
        assert isinstance(rgb, tuple)
        assert len(rgb) == 3
        for ch in rgb:
            assert isinstance(ch, int)
            assert 0 <= ch <= 255


def test_known_colors_correct_rgb() -> None:
    assert resolve_color("red") == (220, 50, 50)
    assert resolve_color("orange") == (240, 140, 50)
    assert resolve_color("yellow") == (240, 210, 50)
    assert resolve_color("green") == (50, 180, 50)
    assert resolve_color("blue") == (50, 80, 220)
    assert resolve_color("purple") == (140, 50, 180)
    assert resolve_color("pink") == (240, 140, 180)
    assert resolve_color("brown") == (139, 90, 43)
    assert resolve_color("gold") == (255, 200, 50)


def test_invalid_color_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not a valid colour"):
        resolve_color("goldenrod")


def test_invalid_color_message_lists_options() -> None:
    with pytest.raises(StudentAPIError) as exc:
        resolve_color("magenta")
    msg = str(exc.value)
    assert "magenta" in msg
    assert "red" in msg
    assert "gold" in msg


def test_color_names_are_case_sensitive() -> None:
    with pytest.raises(StudentAPIError):
        resolve_color("Gold")
    with pytest.raises(StudentAPIError):
        resolve_color("RED")


# ==================================================================
# Character — valid construction
# ==================================================================


def test_character_valid_defaults() -> None:
    ch = Character(name="Explorer")
    assert ch.name == "Explorer"
    assert ch.x == 430
    assert ch.y == 270
    assert ch.color == "gold"
    assert ch.color_rgb == (255, 200, 50)


def test_character_custom_position() -> None:
    ch = Character(name="Hero", x=100, y=200, color="blue")
    assert ch.x == 100
    assert ch.y == 200
    assert ch.color == "blue"
    assert ch.color_rgb == (50, 80, 220)


def test_character_properties_read_only() -> None:
    ch = Character(name="A")
    for attr in ("name", "x", "y", "color", "color_rgb"):
        with pytest.raises(AttributeError):
            setattr(ch, attr, "new")


# ==================================================================
# Character — name validation
# ==================================================================


def test_character_empty_name_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not be empty"):
        Character(name="")


def test_character_whitespace_name_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not be empty"):
        Character(name="   ")


def test_character_non_string_name_rejected() -> None:
    with pytest.raises(StudentAPIError, match="text"):
        Character(name=123)  # type: ignore[arg-type]


# ==================================================================
# Character — coordinate validation
# ==================================================================


def test_character_negative_x_rejected() -> None:
    with pytest.raises(StudentAPIError, match="0 or greater"):
        Character(name="A", x=-5)


def test_character_negative_y_rejected() -> None:
    with pytest.raises(StudentAPIError, match="0 or greater"):
        Character(name="A", y=-1)


def test_character_bool_x_rejected() -> None:
    with pytest.raises(StudentAPIError, match="whole number"):
        Character(name="A", x=True)  # type: ignore[arg-type]


def test_character_bool_y_rejected() -> None:
    with pytest.raises(StudentAPIError, match="whole number"):
        Character(name="A", y=False)  # type: ignore[arg-type]


def test_character_float_x_rejected() -> None:
    with pytest.raises(StudentAPIError, match="whole number"):
        Character(name="A", x=1.5)  # type: ignore[arg-type]


def test_character_float_y_rejected() -> None:
    with pytest.raises(StudentAPIError, match="whole number"):
        Character(name="A", y=2.7)  # type: ignore[arg-type]


# ==================================================================
# Character — colour validation
# ==================================================================


def test_character_invalid_color_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not a valid colour"):
        Character(name="A", color="goldenrod")


def test_character_non_string_color_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not a valid colour"):
        Character(name="A", color=123)  # type: ignore[arg-type]


# ==================================================================
# Character — unknown keyword
# ==================================================================


def test_character_unknown_keyword_rejected() -> None:
    with pytest.raises(TypeError, match="unexpected keyword"):
        Character(name="A", speed=10)  # type: ignore[arg-type]


# ==================================================================
# Object — valid construction
# ==================================================================


def test_object_valid() -> None:
    obj = Object(name="Chest", x=60, y=480, color="brown")
    assert obj.name == "Chest"
    assert obj.x == 60
    assert obj.y == 480
    assert obj.color == "brown"
    assert obj.color_rgb == (139, 90, 43)
    assert obj.near_message is None
    assert obj.interacted_message is None


def test_object_default_color() -> None:
    obj = Object(name="Thing", x=0, y=0)
    assert obj.color == "brown"


def test_object_properties_read_only() -> None:
    obj = Object(name="A", x=0, y=0)
    for attr in ("name", "x", "y", "color", "color_rgb"):
        with pytest.raises(AttributeError):
            setattr(obj, attr, "new")


# ==================================================================
# Object — validation
# ==================================================================


def test_object_empty_name_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not be empty"):
        Object(name="", x=0, y=0)


def test_object_negative_x_rejected() -> None:
    with pytest.raises(StudentAPIError, match="0 or greater"):
        Object(name="A", x=-5, y=0)


def test_object_bool_x_rejected() -> None:
    with pytest.raises(StudentAPIError, match="whole number"):
        Object(name="A", x=True, y=0)  # type: ignore[arg-type]


def test_object_float_y_rejected() -> None:
    with pytest.raises(StudentAPIError, match="whole number"):
        Object(name="A", x=0, y=1.5)  # type: ignore[arg-type]


def test_object_invalid_color_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not a valid colour"):
        Object(name="A", x=0, y=0, color="magenta")


def test_object_unknown_keyword_rejected() -> None:
    with pytest.raises(TypeError, match="unexpected keyword"):
        Object(name="A", x=0, y=0, width=10)  # type: ignore[arg-type]


# ==================================================================
# Object — interaction messages
# ==================================================================


def test_when_near_stores_message() -> None:
    obj = Object(name="A", x=0, y=0)
    obj.when_near("Press E to explore")
    assert obj.near_message == "Press E to explore"


def test_when_interacted_stores_message() -> None:
    obj = Object(name="A", x=0, y=0)
    obj.when_interacted("You found a treasure!")
    assert obj.interacted_message == "You found a treasure!"


def test_when_near_replaces_previous() -> None:
    obj = Object(name="A", x=0, y=0)
    obj.when_near("First")
    obj.when_near("Second")
    assert obj.near_message == "Second"


def test_when_interacted_replaces_previous() -> None:
    obj = Object(name="A", x=0, y=0)
    obj.when_interacted("First")
    obj.when_interacted("Second")
    assert obj.interacted_message == "Second"


def test_when_near_empty_rejected() -> None:
    obj = Object(name="A", x=0, y=0)
    with pytest.raises(StudentAPIError, match="not be empty"):
        obj.when_near("")


def test_when_near_whitespace_rejected() -> None:
    obj = Object(name="A", x=0, y=0)
    with pytest.raises(StudentAPIError, match="not be empty"):
        obj.when_near("   ")


def test_when_interacted_non_string_rejected() -> None:
    obj = Object(name="A", x=0, y=0)
    with pytest.raises(StudentAPIError, match="text"):
        obj.when_interacted(123)  # type: ignore[arg-type]


# ==================================================================
# Object — message combinations
# ==================================================================


def test_neither_message_set() -> None:
    obj = Object(name="A", x=0, y=0)
    assert obj.near_message is None
    assert obj.interacted_message is None


def test_only_near_message_set() -> None:
    obj = Object(name="A", x=0, y=0)
    obj.when_near("Hello")
    assert obj.near_message == "Hello"
    assert obj.interacted_message is None


def test_only_interacted_message_set() -> None:
    obj = Object(name="A", x=0, y=0)
    obj.when_interacted("Success")
    assert obj.near_message is None
    assert obj.interacted_message == "Success"


def test_both_messages_set() -> None:
    obj = Object(name="A", x=0, y=0)
    obj.when_near("Near")
    obj.when_interacted("Interact")
    assert obj.near_message == "Near"
    assert obj.interacted_message == "Interact"


# ==================================================================
# World — valid construction
# ==================================================================


def test_world_creation() -> None:
    w = World("Treasure Island")
    assert w.name == "Treasure Island"
    assert w.character is None
    assert w.object is None


def test_world_empty_name_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not be empty"):
        World("")


def test_world_whitespace_name_rejected() -> None:
    with pytest.raises(StudentAPIError, match="not be empty"):
        World("   ")


# ==================================================================
# World — add Character
# ==================================================================


def test_world_add_character() -> None:
    w = World("W")
    ch = Character(name="Hero")
    w.add(ch)
    assert w.character is ch


def test_world_add_second_character_rejected() -> None:
    w = World("W")
    ch1 = Character(name="A")
    ch2 = Character(name="B")
    w.add(ch1)
    with pytest.raises(StudentAPIError, match="already has a character"):
        w.add(ch2)


def test_world_second_character_error_message() -> None:
    w = World("W")
    w.add(Character(name="A"))
    with pytest.raises(StudentAPIError) as exc:
        w.add(Character(name="B"))
    assert "one character at a time" in str(exc.value)


# ==================================================================
# World — add Object
# ==================================================================


def test_world_add_object() -> None:
    w = World("W")
    obj = Object(name="Chest", x=0, y=0)
    w.add(obj)
    assert w.object is obj


def test_world_add_second_object_rejected() -> None:
    w = World("W")
    obj1 = Object(name="A", x=0, y=0)
    obj2 = Object(name="B", x=100, y=100)
    w.add(obj1)
    with pytest.raises(StudentAPIError, match="already has an object"):
        w.add(obj2)


def test_world_add_wrong_type_rejected() -> None:
    w = World("W")
    with pytest.raises(StudentAPIError, match="Character or an Object"):
        w.add("not an entity")  # type: ignore[arg-type]


# ==================================================================
# World — registration order
# ==================================================================


def test_configure_before_add() -> None:
    w = World("W")
    obj = Object(name="Chest", x=0, y=0)
    obj.when_near("Hello")
    w.add(obj)
    assert w.object is obj
    assert w.object.near_message == "Hello"


def test_add_before_configure() -> None:
    w = World("W")
    obj = Object(name="Chest", x=0, y=0)
    w.add(obj)
    obj.when_near("Hello")
    assert w.object.near_message == "Hello"


def test_character_and_object_both_added() -> None:
    w = World("W")
    ch = Character(name="A")
    obj = Object(name="B", x=0, y=0)
    w.add(ch)
    w.add(obj)
    assert w.character is ch
    assert w.object is obj


# ==================================================================
# World — run() deferred
# ==================================================================


def test_world_run_raises_not_implemented() -> None:
    w = World("W")
    w.add(Character(name="A"))
    w.add(Object(name="B", x=0, y=0))
    with pytest.raises(NotImplementedError, match="Task M4C"):
        w.run()


def test_world_run_message_mentions_future() -> None:
    w = World("W")
    w.add(Character(name="A"))
    w.add(Object(name="B", x=0, y=0))
    with pytest.raises(NotImplementedError) as exc:
        w.run()
    assert "M4C" in str(exc.value)


# ==================================================================
# StudentAPIError — chaining
# ==================================================================


def test_student_api_error_chains_internal_exception() -> None:
    try:
        try:
            raise ValueError("internal engine failure")
        except ValueError as exc:
            raise StudentAPIError("Something went wrong.") from exc
    except StudentAPIError as api_exc:
        assert api_exc.__cause__ is not None
        assert isinstance(api_exc.__cause__, ValueError)
        assert "internal engine failure" in str(api_exc.__cause__)


def test_student_api_error_is_exception() -> None:
    assert issubclass(StudentAPIError, Exception)


# ==================================================================
# Public API surface
# ==================================================================


def test_explore_package_exports() -> None:
    import explore

    assert hasattr(explore, "World")
    assert hasattr(explore, "Character")
    assert hasattr(explore, "Object")
    assert hasattr(explore, "StudentAPIError")


def test_explore_package_no_engine_exports() -> None:
    """Students should not see engine internals through the explore package."""
    import explore

    assert not hasattr(explore, "App")
    assert not hasattr(explore, "Config")
    assert not hasattr(explore, "Renderer")
    assert not hasattr(explore, "Platform")


# ==================================================================
# Regression — engine tests must still pass
# ==================================================================
# (Verified by running full test suite — engine is untouched.)
