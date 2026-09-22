"""S26: every mechanic you may choose from, and which ones can read each other.

This file is a menu and a feasibility probe. It is **not** capstone code, and
there is nothing in it for you to finish. Run it, read the list, and check that
the mechanics your blueprint names are mechanics the runtime really has:

```console
python lessons/sessions/s26/student/mechanic_menu.py
```

Every entry below already exists in the course runtime, and every one of them
is something you built at least once in S07-S25. S26 adds no new engine
feature, and neither does your capstone. If your premise seems to need
something that is not on this list, the thing to change is the wording of the
premise, not the engine.

Two mechanics are **connected** when one of them can really read the other:
a counter and the character that compares it to its goal, a switch and the
character that answers differently while it is on. Two mechanics that sit in
the same folder and never look at each other are decorations, not a system.
``connectable_pairs`` below is the exact list the blueprint checker accepts.

Sharing a look is not reading. ``toggle_style`` is one switch appearance reused
by several switches, so a styled switch is still just a switch: the character
who answers differently is what makes it a system. That is why ``toggle`` and
``toggle_style`` together are **not** a connected pair, while ``toggle_style``
and any of the characters that watch a switch are.
"""

from __future__ import annotations

#: One entry per mechanic you may put in ``capstone-blueprint.yaml``.
#:
#: * ``mission`` - where you first met it;
#: * ``lives_on`` - whether it belongs to a world object or to a character;
#: * ``needs`` - what your capstone will have to author for this mechanic to be
#:   real. You design it in S26 and build towards it from S27; the package YAML
#:   that carries it is authored in S28;
#: * ``reads`` - the mechanics this one can notice. An empty tuple means this
#:   mechanic produces something; it does not watch anything itself. Reusing a
#:   named look is not noticing, so ``toggle_style`` reads nothing.
SUPPORTED_MECHANICS = {
    "response": {
        "mission": "M03",
        "lives_on": "world object",
        "needs": "when_near and when_interacted text you write",
        "reads": (),
        "summary": "An object that answers when the player comes close and touches it.",
    },
    "dialogue": {
        "mission": "M04/M05",
        "lives_on": "character",
        "needs": "a greeting, or a 2-3 line conversation",
        "reads": (),
        "summary": "A character who says something when the player talks to them.",
    },
    "toggle": {
        "mission": "M07",
        "lives_on": "world object",
        "needs": "off_color and on_color, and no plain color line",
        "reads": (),
        "summary": "A switch the player flips between two colors.",
    },
    "toggle_style": {
        "mission": "M14",
        "lives_on": "world object",
        "needs": "one named style reused by at least two toggle objects",
        "reads": (),
        "summary": "One switch look shared by several switches.",
    },
    "counter": {
        "mission": "M09",
        "lives_on": "world object",
        "needs": "a goal from 2 through 5 and a goal-reached message",
        "reads": (),
        "summary": "An object that counts how many times it was touched.",
    },
    "respond_to_toggle": {
        "mission": "M08/M12",
        "lives_on": "character",
        "needs": "one toggle object id, plus when_off and when_on lines",
        "reads": ("toggle", "toggle_style"),
        "summary": "A character who answers one way while a switch is off, another while it is on.",
    },
    "respond_to_two_toggles": {
        "mission": "M10",
        "lives_on": "character",
        "needs": "exactly two toggle object ids, plus the two answers",
        "reads": ("toggle", "toggle_style"),
        "summary": "A character who opens up only once BOTH switches are on.",
    },
    "respond_to_either_toggle": {
        "mission": "M11",
        "lives_on": "character",
        "needs": "exactly two toggle object ids, plus the two answers",
        "reads": ("toggle", "toggle_style"),
        "summary": "A character who opens up as soon as EITHER switch is on.",
    },
    "respond_to_counter": {
        "mission": "M13",
        "lives_on": "character",
        "needs": "one counter object id, plus a below-goal and an at-goal line",
        "reads": ("counter",),
        "summary": "A character who compares a counter with its goal.",
    },
    "respond_to_sequence": {
        "mission": "M15",
        "lives_on": "character",
        "needs": "exactly three world object ids in order, plus the two answers",
        "reads": ("response", "toggle", "toggle_style", "counter"),
        "summary": "A character who unlocks when three objects are touched in the right order.",
    },
}

#: Things the runtime does not have. No capstone may depend on one of these,
#: and no amount of YAML will add one. Reword the premise instead.
UNSUPPORTED = (
    "progress saved between sessions",
    "an inventory or a bag of items",
    "collision, locking, or blocked movement",
    "health, currency, or a general score",
    "a variable the player can set to anything",
    "timers or anything that happens on its own",
    "more than one player at once",
    "one package reading another package's state",
)

#: Ceilings for a capstone that can actually be finished by S30.
MECHANIC_LIMITS = (2, 4)
KEY_ELEMENT_LIMITS = (2, 4)
PLAYER_FLOW_LIMITS = (3, 6)


def is_supported(kind) -> bool:
    """Is ``kind`` a mechanic the current runtime really has?"""
    return isinstance(kind, str) and kind in SUPPORTED_MECHANICS


def reads(kind) -> tuple[str, ...]:
    """Which mechanics ``kind`` can notice. Empty means it notices nothing."""
    if not is_supported(kind):
        return ()
    return SUPPORTED_MECHANICS[kind]["reads"]


def can_connect(first, second) -> bool:
    """True when one of these two mechanics can really read the other."""
    if not (is_supported(first) and is_supported(second)) or first == second:
        return False
    return first in reads(second) or second in reads(first)


def connectable_pairs() -> tuple[tuple[str, str], ...]:
    """Every pair of mechanics the runtime can genuinely connect, sorted."""
    kinds = sorted(SUPPORTED_MECHANICS)
    return tuple(
        (first, second)
        for index, first in enumerate(kinds)
        for second in kinds[index + 1 :]
        if can_connect(first, second)
    )


def main() -> None:
    print("S26 mechanic menu - everything your capstone may use, and nothing else.\n")
    for kind, entry in SUPPORTED_MECHANICS.items():
        print(f"  {kind}  ({entry['mission']}, lives on a {entry['lives_on']})")
        print(f"      {entry['summary']}")
        print(f"      you will author: {entry['needs']}")
    low, high = MECHANIC_LIMITS
    print(f"\nChoose {low} to {high} of them. At least two must be a connected pair:\n")
    for first, second in connectable_pairs():
        print(f"  {first} + {second}")
    print("\nThe runtime does NOT have:")
    for absent in UNSUPPORTED:
        print(f"  - {absent}")
    print("\nIf your premise needs one of those, change the premise, not the engine.")
    print("Then fill in capstone-blueprint.yaml and run the blueprint checker.")


if __name__ == "__main__":
    main()
