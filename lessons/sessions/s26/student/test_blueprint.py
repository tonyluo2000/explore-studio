"""S26 blueprint checker - is my capstone design finished and buildable?

Run it as often as you like. It starts red, and that is correct: on the
download every answer is still a ``CHOOSE-ME``, so the checker is counting
decisions you have not made yet, not bugs.

```console
python -m pytest -q lessons/sessions/s26/student/test_blueprint.py
```

Each failure is one of three different things, and the test name tells you
which:

* ``test_no_unmade_decisions`` - a ``CHOOSE-ME`` is still sitting where your
  words belong. The message names the exact line.
* ``test_mechanics_*`` / ``test_two_mechanics_are_really_connected`` /
  ``test_nothing_needs_a_feature_the_runtime_does_not_have`` - your design asks
  for something the runtime cannot do, or for more than you can finish. Change
  the design; ``mechanic_menu.py`` lists what exists.
* ``test_player_flow_*`` / ``test_s27_first_slice_is_bounded`` /
  ``test_risk_and_fallback_are_named`` - the plan is not concrete enough yet
  for S27 to start from it.

This checker never reads your premise for quality. It has no opinion about
what you should make, and it cannot tell a good idea from a dull one. It only
asks whether you made the decisions, whether the mechanics exist, and whether
the plan is small enough to finish by S30.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import yaml

STUDENT_ROOT = Path(__file__).resolve().parent
if str(STUDENT_ROOT) not in sys.path:  # so `mechanic_menu` imports from any folder
    sys.path.insert(0, str(STUDENT_ROOT))

import mechanic_menu  # noqa: E402  (needs the path above)

PLACEHOLDER = "CHOOSE-ME"

#: Normally my own blueprint. The teacher can point the checker at one of the
#: examples instead, to show the gate catching an over-scoped plan:
#: ``BLUEPRINT=.../examples/too-big-blueprint.yaml python -m pytest ...``
BLUEPRINT_PATH = Path(os.environ.get("BLUEPRINT") or STUDENT_ROOT / "capstone-blueprint.yaml")

MIN_MECHANICS, MAX_MECHANICS = mechanic_menu.MECHANIC_LIMITS
MIN_ELEMENTS, MAX_ELEMENTS = mechanic_menu.KEY_ELEMENT_LIMITS
MIN_FLOW_STEPS, MAX_FLOW_STEPS = mechanic_menu.PLAYER_FLOW_LIMITS

#: Phrases that mean "I have not scoped this yet". An S27 target has to name
#: one slice; these name the whole project.
UNBOUNDED_TARGET_PHRASES = (
    "whole game",
    "whole project",
    "whole thing",
    "entire game",
    "entire project",
    "all of it",
    "everything",
    "finish the capstone",
    "build the capstone",
)

#: Features the runtime genuinely does not have, in the words a student is most
#: likely to write. Each one is paired with a mechanic that *does* exist, so the
#: failure is a redesign prompt rather than a dead end. This list is short on
#: purpose: the real guard on unsupported behaviour is the ``mechanics:`` field,
#: which accepts nothing outside the menu.
_NOT_REMEMBERED = "nothing is remembered between sessions; the flow has to finish in one visit"
_ON_ITS_OWN = "nothing happens on its own; every change comes from a player interaction"
_ONE_WORLD = "one world, one package; make the single space better instead"

UNSUPPORTED_PHRASES = {
    "inventory": "there is no inventory; a toggle can stand for 'I have this' instead",
    "save my progress": _NOT_REMEMBERED,
    "save progress": _NOT_REMEMBERED,
    "saves progress": _NOT_REMEMBERED,
    "saved progress": _NOT_REMEMBERED,
    "health bar": "there is no health; a counter with a goal is the closest real mechanic",
    "multiplayer": "one player at a time; write the flow for a single visitor",
    "timer": _ON_ITS_OWN,
    "countdown": _ON_ITS_OWN,
    "log in": "there are no accounts; a visitor just walks in",
    "second level": _ONE_WORLD,
    "next level": _ONE_WORLD,
}


def unfilled(value, path: str = "") -> list[str]:
    """Return the dotted path of every answer still holding a placeholder."""
    if isinstance(value, str):
        return [path] if PLACEHOLDER in value else []
    if isinstance(value, dict):
        return [
            item
            for key, child in value.items()
            for item in unfilled(child, f"{path}.{key}" if path else str(key))
        ]
    if isinstance(value, (list, tuple)):
        return [
            item
            for index, child in enumerate(value)
            for item in unfilled(child, f"{path}[{index}]")
        ]
    return []


def answered(value) -> bool:
    """Is this a real written answer rather than a blank or a placeholder?"""
    return isinstance(value, str) and value.strip() != "" and PLACEHOLDER not in value


def mechanic_kinds(document) -> list:
    """The `kind:` of every mechanic listed, in blueprint order."""
    mechanics = document.get("mechanics")
    if not isinstance(mechanics, list):
        return []
    return [entry.get("kind") for entry in mechanics if isinstance(entry, dict)]


def unsupported_phrases_in(document) -> list[str]:
    """Every unsupported feature this blueprint's prose asks for, with the fix."""
    text = yaml.safe_dump(document, allow_unicode=True).lower()
    return [
        f"{phrase!r}: {advice}" for phrase, advice in UNSUPPORTED_PHRASES.items() if phrase in text
    ]


@pytest.fixture(scope="module")
def blueprint() -> dict:
    document = yaml.safe_load(BLUEPRINT_PATH.read_text(encoding="utf-8"))
    assert isinstance(document, dict), f"{BLUEPRINT_PATH.name} must stay a YAML mapping"
    for section in (
        "project",
        "mechanics",
        "world",
        "integration",
        "build_plan",
        "risk",
        "reflection",
    ):
        assert section in document, f"{BLUEPRINT_PATH.name} is missing its `{section}:` section"
    return document


# --- Did I make my decisions? ------------------------------------------------


def test_no_unmade_decisions(blueprint):
    missing = unfilled(blueprint)
    assert not missing, (
        "Your blueprint still has unmade decisions:\n  "
        + "\n  ".join(missing)
        + f"\nEach one is a line in {BLUEPRINT_PATH.name} that still says {PLACEHOLDER}."
    )


def test_premise_and_player_goal_are_specific(blueprint):
    project = blueprint["project"]
    for field in ("title", "premise", "player_goal"):
        assert answered(project.get(field)), f"project.{field} is still blank"
    assert len(project["premise"].split()) >= 10, (
        "project.premise reads like a title, not a premise. Two or three "
        "sentences: what is this place, and why would a visitor come?"
    )
    assert len(project["player_goal"].split()) >= 5, (
        "project.player_goal has to be something somebody watching could see "
        "happen. Name the moment, not the mood."
    )


# --- Do my mechanics exist, and are there the right number of them? ----------


def test_mechanics_are_two_to_four_supported_kinds(blueprint):
    kinds = mechanic_kinds(blueprint)
    assert MIN_MECHANICS <= len(kinds) <= MAX_MECHANICS, (
        f"A capstone you can finish by S30 uses {MIN_MECHANICS} to {MAX_MECHANICS} "
        f"mechanics; this blueprint lists {len(kinds)}. If you are over, cut the "
        "one that carries the least of the player's experience."
    )
    unsupported = [kind for kind in kinds if not mechanic_menu.is_supported(kind)]
    assert not unsupported, (
        f"The runtime has no {unsupported!r}. Run mechanic_menu.py for the list "
        "of mechanics that exist, and pick the closest one - or reword the "
        "premise so it does not need this."
    )
    assert len(set(kinds)) == len(kinds), (
        f"The same mechanic is listed twice ({kinds}). Four entries that are "
        "really two mechanics is still two mechanics; list each kind once."
    )


def test_every_mechanic_has_a_role_in_the_player_experience(blueprint):
    for index, entry in enumerate(blueprint["mechanics"]):
        kind = entry.get("kind")
        role = entry.get("role_in_experience")
        assert answered(role), f"mechanics[{index}] ({kind}) has no role_in_experience yet"
        assert len(role.split()) >= 5, (
            f"mechanics[{index}].role_in_experience only names the mechanic. Say "
            f"what {kind} does for the player, in one sentence."
        )


def test_two_mechanics_are_really_connected(blueprint):
    integration = blueprint["integration"]
    pair = integration.get("connected_mechanics")
    kinds = mechanic_kinds(blueprint)

    assert isinstance(pair, list) and len(pair) == 2, (
        "integration.connected_mechanics names exactly two of your mechanics: "
        "the one that changes something, and the one that notices."
    )
    absent = [kind for kind in pair if kind not in kinds]
    assert not absent, (
        f"integration.connected_mechanics names {absent!r}, which is not in your "
        f"own mechanics list ({kinds})."
    )
    assert mechanic_menu.can_connect(*pair), (
        f"The runtime cannot connect {pair[0]!r} and {pair[1]!r}: neither one can "
        "read the other, so they would be two decorations side by side rather "
        "than one system. mechanic_menu.py prints every pair that really works:\n  "
        + "\n  ".join(f"{first} + {second}" for first, second in mechanic_menu.connectable_pairs())
    )
    assert answered(
        integration.get("how_mechanics_connect")
    ), "integration.how_mechanics_connect is still blank"
    assert len(integration["how_mechanics_connect"].split()) >= 8, (
        "integration.how_mechanics_connect has to say what the second mechanic "
        "notices, and when. 'They are both in my package' is not a connection."
    )
    assert answered(integration.get("observable_success")), (
        "integration.observable_success is still blank. Name what the player "
        "sees or reads at the moment they succeed."
    )


# --- Is the world small, and is the flow concrete? ---------------------------


def test_world_has_two_to_four_key_elements(blueprint):
    elements = blueprint["world"].get("key_elements")
    assert isinstance(elements, list), "world.key_elements must stay a list"
    assert MIN_ELEMENTS <= len(elements) <= MAX_ELEMENTS, (
        f"Every key element is a file you author later. Keep {MIN_ELEMENTS} to "
        f"{MAX_ELEMENTS}; this blueprint lists {len(elements)}."
    )
    for index, element in enumerate(elements):
        assert answered(element.get("name")), f"world.key_elements[{index}] has no name"
        assert answered(element.get("role")), (
            f"world.key_elements[{index}] ({element.get('name')}) has no role. "
            "What does the visitor do with it, or learn from it?"
        )


def test_player_flow_is_three_to_six_concrete_steps(blueprint):
    flow = blueprint["world"].get("player_flow")
    assert isinstance(flow, list), "world.player_flow must stay a list of steps"
    assert MIN_FLOW_STEPS <= len(flow) <= MAX_FLOW_STEPS, (
        f"A flow the player can actually follow is {MIN_FLOW_STEPS} to "
        f"{MAX_FLOW_STEPS} steps; this one has {len(flow)}. Fewer steps than "
        "three is not a flow, and more than six is a second project."
    )
    for index, step in enumerate(flow):
        assert answered(step), f"world.player_flow[{index}] is still blank"
        assert len(step.split()) >= 4, (
            f"world.player_flow[{index}] is too short to follow: {step!r}. Say "
            "what the player does, or what changes."
        )


# --- Can S27 start from this tomorrow? --------------------------------------


def test_s27_first_slice_is_bounded(blueprint):
    plan = blueprint["build_plan"]
    target = plan.get("s27_target")
    assert answered(target), "build_plan.s27_target is still blank"
    unbounded = [phrase for phrase in UNBOUNDED_TARGET_PHRASES if phrase in target.lower()]
    assert not unbounded, (
        f"build_plan.s27_target says {unbounded[0]!r}, which is the project, not "
        "a slice of it. Name ONE thing you could finish and test in a single "
        "session - two objects, or one interaction that validates and plays."
    )
    for field in ("validation_plan", "play_test_plan"):
        assert answered(plan.get(field)), f"build_plan.{field} is still blank"


def test_risk_and_fallback_are_named(blueprint):
    risk = blueprint["risk"]
    assert answered(risk.get("biggest_risk")), (
        "risk.biggest_risk is still blank. Every real plan has one; naming it is " "not pessimism."
    )
    assert answered(risk.get("fallback_if_time_runs_short")), (
        "risk.fallback_if_time_runs_short is still blank. Decide now what you "
        "would cut first, while you are calm and it is cheap."
    )


def test_nothing_needs_a_feature_the_runtime_does_not_have(blueprint):
    asked_for = unsupported_phrases_in(blueprint)
    assert not asked_for, (
        "Your blueprint asks for something the runtime does not have:\n  "
        + "\n  ".join(asked_for)
        + "\nThe fix is the wording of the design, not the engine."
    )


# --- Can I explain why? ------------------------------------------------------


def test_reflection_explains_the_choice(blueprint):
    reflection = blueprint["reflection"]
    for field in ("why_this_project", "hardest_design_decision"):
        assert answered(reflection.get(field)), f"reflection.{field} is still blank"
    assert len(reflection["hardest_design_decision"].split()) >= 8, (
        "reflection.hardest_design_decision should name the decision and what "
        "you decided - one sentence is enough."
    )
