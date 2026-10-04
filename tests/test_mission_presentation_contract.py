"""Canonical expected-presentation contract for every shipped Trail session.

Moon Meadow eligibility is an explicit allow-list
(``engine.rendering._mission_presentation.MISSION_PRESENTATIONS``) and trusted
art is keyed by exact package qualified ids, so a session can silently fall
back to the plain Trail. This module pins, per session, what the canonical
``explore-package trail`` command on the student task card must show.

The standard Trail is a legitimate choice: only listed ``moon-meadow`` sessions
must show Moon Meadow. To opt a session (S04+) in deliberately:

1. add its mission to ``MISSION_PRESENTATIONS`` (with any ``sprite_aliases``);
2. change its row in ``EXPECTED_PRESENTATION`` to ``MOON_MEADOW``;
3. list the qualified ids that must wear trusted art in ``REQUIRED_TRUSTED_ART``.

A new session whose task card gains a trail command must get a row here too.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

from engine.assets import TrustedArtCatalog
from engine.rendering._classroom_environment import MEADOW_BACKDROP
from engine.rendering._classroom_sprites import (
    COMPASS_SHEET_ID,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
    SPRITE_SHEET_IDS,
)
from engine.rendering._mission_presentation import mission_presentation
from engine.rendering._trail_presentation import TrailPresentation
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from scripts.make_my_world import S02_PACKAGE_SEED, STUDENT_S02_PACKAGE, WORKSPACE_NAME
from tests.test_s02_art_pass import ArtRenderer

REPO = Path(__file__).resolve().parents[1]
SESSIONS = REPO / "lessons/sessions"
SLIDES = REPO / "course4teen-website/app/students/slides"
STANDARD, MOON_MEADOW = "standard", "moon-meadow"

#: session -> (canonical --mission-id, presentation the runtime gives it today).
EXPECTED_PRESENTATION: dict[str, tuple[str, str]] = {
    "s01": ("visit-all-classroom-objects", STANDARD),
    "s02": ("create-a-classroom-object", MOON_MEADOW),
    "s03": ("make-your-object-respond", MOON_MEADOW),
    "s04": ("introduce-your-character", STANDARD),
    "s05": ("write-a-short-conversation", STANDARD),
    "s06": ("build-an-object-collection", STANDARD),
    "s07": ("toggle-an-object-state", STANDARD),
    "s08": ("respond-to-object-state", STANDARD),
    "s09": ("count-object-interactions", STANDARD),
    "s10": ("compare-a-counter-to-its-goal", STANDARD),
    "s11": ("require-all-switches-on", STANDARD),
    "s12": ("open-with-either-switch", STANDARD),
    "s13": ("invert-a-switch-condition", STANDARD),
    "s14": ("reuse-a-named-toggle-style", STANDARD),
    "s15": ("complete-actions-in-order", STANDARD),
    "s16": ("build-an-object-collection", STANDARD),
    "s17": ("build-an-object-collection", STANDARD),
    "s18": ("compare-a-counter-to-its-goal", STANDARD),
    "s19": ("complete-actions-in-order", STANDARD),
    "s20": ("complete-actions-in-order", STANDARD),
    "s21": ("build-an-object-collection", STANDARD),
    "s22": ("respond-to-object-state", STANDARD),
    "s23": ("reuse-a-named-toggle-style", STANDARD),
    "s24": ("complete-actions-in-order", STANDARD),
    "s25": ("complete-actions-in-order", STANDARD),
    "s27": ("build-an-object-collection", STANDARD),
    "s28": ("reuse-a-named-toggle-style", STANDARD),
    "s30": ("present-your-capstone-expedition", STANDARD),
}

#: Moon Meadow session -> package qualified ids that must draw trusted art.
REQUIRED_TRUSTED_ART: dict[str, tuple[str, ...]] = {
    "s02": (
        NOVA_QUALIFIED_ID,
        PIXEL_QUALIFIED_ID,
        CRYSTAL_LANTERN_QUALIFIED_ID,
        MOON_COMPASS_QUALIFIED_ID,
    ),
    "s03": (NOVA_QUALIFIED_ID, "moon-compass-response:compass"),
}

#: Student Workspace copies named on task cards -> the Course Kit seed they start from.
STUDENT_COPY_SEEDS = {Path("..", WORKSPACE_NAME, STUDENT_S02_PACKAGE): REPO / S02_PACKAGE_SEED}

MOON_MEADOW_SESSIONS = sorted(
    session for session, (_, kind) in EXPECTED_PRESENTATION.items() if kind == MOON_MEADOW
)


def _trail_commands(card: Path) -> list[tuple[tuple[str, ...], dict[str, str]]]:
    """Each ``explore-package trail`` command as (package args, ``--option`` values)."""
    joined = re.sub(r"\\\n", " ", card.read_text(encoding="utf-8"))
    commands = []
    for line in joined.splitlines():
        if not line.strip().startswith("explore-package trail "):
            continue
        tokens = shlex.split(line.strip())
        packages: list[str] = []
        options: dict[str, str] = {}
        rest = iter(tokens[2:])
        for token in rest:
            if token.startswith("--"):
                options[token] = next(rest)
            else:
                packages.append(token)
        commands.append((tuple(packages), options))
    return commands


def _canonical_commands() -> dict[str, tuple[tuple[str, ...], dict[str, str]]]:
    found = {}
    for card in sorted(SESSIONS.glob("s*/student/task-card.md")):
        commands = [c for c in _trail_commands(card) if "--mission-id" in c[1]]
        if commands:
            assert len(commands) == 1, f"{card}: expected one canonical trail command"
            found[card.parts[-3]] = commands[0]
    return found


CANONICAL = _canonical_commands()


def _package_root(argument: str) -> Path:
    path = Path(argument)
    if path in STUDENT_COPY_SEEDS:
        return STUDENT_COPY_SEEDS[path]
    assert (
        not path.is_absolute() and ".." not in path.parts
    ), f"{argument} is outside the Course Kit; map it to its seed in STUDENT_COPY_SEEDS"
    return REPO / path


class AccentCheckingRenderer(ArtRenderer):
    """Refuses a trusted frame for the wrong accent, exactly like the real Renderer."""

    catalog = TrustedArtCatalog()

    def draw_sprite_frame(self, asset_id, row, column, *values, **options):  # type: ignore[no-untyped-def]
        accent = options.get("accent")
        spec = self.catalog.spec(asset_id)
        if spec is None or (accent is not None and spec.accent != accent):
            return False
        return super().draw_sprite_frame(asset_id, row, column, *values, **options)


def _trusted_sheet(identity: str | None) -> str | None:
    if identity == MOON_COMPASS_QUALIFIED_ID:
        return COMPASS_SHEET_ID
    return SPRITE_SHEET_IDS.get(identity) if identity is not None else None


# ---------------------------------------------------------------------------
# The contract matches the task cards and the runtime policy
# ---------------------------------------------------------------------------


def test_every_canonical_trail_command_has_an_explicit_expectation() -> None:
    assert sorted(CANONICAL) == sorted(EXPECTED_PRESENTATION), (
        "A task card's canonical trail command was added or removed: "
        "update EXPECTED_PRESENTATION explicitly."
    )
    for session, (_, options) in CANONICAL.items():
        assert options["--mission-id"] == EXPECTED_PRESENTATION[session][0], session


@pytest.mark.parametrize("session", sorted(EXPECTED_PRESENTATION))
def test_runtime_presentation_matches_the_contract(session: str) -> None:
    mission_id, kind = EXPECTED_PRESENTATION[session]
    assert kind in (STANDARD, MOON_MEADOW)
    gets_moon_meadow = mission_presentation(mission_id) is not None
    assert gets_moon_meadow == (kind == MOON_MEADOW), (session, mission_id)
    assert TrailPresentation(mission_id).active == gets_moon_meadow


def test_required_art_is_declared_for_exactly_the_moon_meadow_sessions() -> None:
    assert sorted(REQUIRED_TRUSTED_ART) == MOON_MEADOW_SESSIONS
    assert all(REQUIRED_TRUSTED_ART.values())


# ---------------------------------------------------------------------------
# Moon Meadow sessions really draw it from their canonical packages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("session", MOON_MEADOW_SESSIONS)
def test_required_objects_resolve_to_trusted_sprite_identities(session: str) -> None:
    presentation = TrailPresentation(EXPECTED_PRESENTATION[session][0])
    for qualified_id in REQUIRED_TRUSTED_ART[session]:
        identity = presentation.sprite_identity(qualified_id)
        assert _trusted_sheet(identity) is not None, (session, qualified_id, identity)
        assert presentation.pose_for(qualified_id) is not None, (session, qualified_id)


@pytest.mark.parametrize("session", MOON_MEADOW_SESSIONS)
def test_canonical_command_draws_moon_meadow_and_trusted_art(session: str) -> None:
    packages, options = CANONICAL[session]
    roots = [_package_root(argument) for argument in packages]
    assert all(root.is_dir() for root in roots), roots
    planned = plan_local_classroom_trail(roots, player_qualified_id=options["--player"])
    assert planned.is_planned, planned.issues
    renderer = AccentCheckingRenderer()
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=options["--mission-id"])
    scene.enter()
    scene.render()

    sprites = [values for kind, values in renderer.operations if kind == "sprite"]
    assert sprites and sprites[0][:3] == MEADOW_BACKDROP, "Moon Meadow backdrop not drawn"

    entities = {options["--player"]: scene.player}
    entities.update((npc.qualified_id, npc.character) for npc in scene.npcs)
    entities.update((item.qualified_id, item.world_object) for item in scene.objects)
    presentation = TrailPresentation(options["--mission-id"])
    for qualified_id in REQUIRED_TRUSTED_ART[session]:
        assert qualified_id in entities, f"{session}: {qualified_id} is not in the scene"
        entity = entities[qualified_id]
        sheet = _trusted_sheet(presentation.sprite_identity(qualified_id))
        drawn = [values for values in sprites if values[0] == sheet and values[3] == entity.x]
        assert drawn, f"{session}: {qualified_id} fell back instead of drawing {sheet}"
        assert all(values[5:7] == (entity.width, entity.height) for values in drawn)
        box = (entity.x, entity.y, entity.width, entity.height, entity.color)
        assert ("rect", box) not in renderer.operations, f"{session}: {qualified_id} rectangle"


# ---------------------------------------------------------------------------
# Student slides never promise a presentation the runtime does not deliver
# ---------------------------------------------------------------------------


def test_only_moon_meadow_sessions_promise_moon_meadow_on_their_slides() -> None:
    checked = 0
    for page in sorted(SLIDES.glob("s*/page.tsx")):
        session = page.parent.name
        if session not in EXPECTED_PRESENTATION:
            continue
        checked += 1
        if "Moon Meadow" in page.read_text(encoding="utf-8"):
            assert (
                EXPECTED_PRESENTATION[session][1] == MOON_MEADOW
            ), f"{page} names Moon Meadow but {session} uses the standard Trail"
    assert checked, "no student slide pages were found"
