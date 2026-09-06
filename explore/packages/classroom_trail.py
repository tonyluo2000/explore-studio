"""Planning and local execution for Classroom Trail contract v0.5.

Each input package is first checked through the unchanged v0.1 package-set
contract. The additive trail contract permits multiple characters and world
objects across that validated boundary, with one explicitly selected player.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Final

from explore._colors import resolve_color
from explore.packages.classroom_trail_models import (
    SUPPORTED_CLASSROOM_TRAIL_CONTRACT_VERSION,
    ClassroomTrailPlan,
    ClassroomTrailPlanIssue,
    ClassroomTrailPlanIssueCode,
    ClassroomTrailPlanResult,
)
from explore.packages.loader import load_explorer_package
from explore.packages.package_set_models import PackageSelection, SelectedPackagePlan
from explore.packages.package_set_planner import _build_package_set_plan
from explore.packages.registration_adapter import plan_loaded_explorer_package
from explore.packages.registration_models import (
    CharacterRegistration,
    WorldObjectRegistration,
)

if TYPE_CHECKING:
    from engine.scenes import ClassroomTrailScene

DEFAULT_CLASSROOM_TRAIL_MISSION_ID: Final = "visit-all-classroom-objects"


def _issue(
    code: ClassroomTrailPlanIssueCode,
    message: str,
    location: str,
    *,
    package_id: str | None = None,
    qualified_id: str | None = None,
) -> ClassroomTrailPlanIssue:
    return ClassroomTrailPlanIssue(code, message, location, package_id, qualified_id)


def build_classroom_trail_plan(
    selections: Iterable[PackageSelection],
    *,
    player_qualified_id: str | None = None,
) -> ClassroomTrailPlanResult:
    """Build a canonical v0.5 trail without changing v0.1 cardinality."""
    if isinstance(selections, (str, bytes)):
        raise TypeError("selections must be an iterable of PackageSelection values")
    try:
        candidates = tuple(selections)
    except TypeError as error:
        raise TypeError("selections must be an iterable of PackageSelection values") from error
    if not candidates:
        return ClassroomTrailPlanResult(
            None,
            (
                _issue(
                    ClassroomTrailPlanIssueCode.PACKAGE_SET_REQUIRED,
                    "selections must contain at least one package selection.",
                    "selections",
                ),
            ),
        )

    package_set = _build_package_set_plan(
        candidates,
        maximum_characters=None,
        maximum_world_objects=None,
        cardinality_contract="Classroom Trail v0.5 supports",
    )
    if not package_set.is_planned or package_set.plan is None:
        return ClassroomTrailPlanResult(
            None,
            tuple(
                _issue(
                    ClassroomTrailPlanIssueCode.PACKAGE_INVALID,
                    issue.message,
                    issue.location,
                    package_id=issue.package_id,
                    qualified_id=issue.qualified_id,
                )
                for issue in package_set.issues
            ),
        )

    packages = package_set.plan.packages
    entries = package_set.plan.entries

    characters = tuple(
        sorted(
            (entry for entry in entries if type(entry) is CharacterRegistration),
            key=lambda entry: entry.qualified_id,
        )
    )
    world_objects = tuple(
        sorted(
            (entry for entry in entries if type(entry) is WorldObjectRegistration),
            key=lambda entry: entry.qualified_id,
        )
    )
    issues: list[ClassroomTrailPlanIssue] = []
    player: CharacterRegistration | None = None
    if not characters:
        issues.append(
            _issue(
                ClassroomTrailPlanIssueCode.PLAYER_REQUIRED,
                "A Classroom Trail requires at least one loaded character.",
                "selections",
            )
        )
    elif not isinstance(player_qualified_id, str) or not player_qualified_id.strip():
        issues.append(
            _issue(
                ClassroomTrailPlanIssueCode.PLAYER_SELECTION_REQUIRED,
                "player_qualified_id must explicitly select one loaded character.",
                "player_qualified_id",
            )
        )
    else:
        player = next(
            (
                character
                for character in characters
                if character.qualified_id == player_qualified_id
            ),
            None,
        )
        if player is None:
            issues.append(
                _issue(
                    ClassroomTrailPlanIssueCode.PLAYER_SELECTION_NOT_FOUND,
                    (
                        f'player_qualified_id "{player_qualified_id}" does not identify '
                        "a loaded character in this trail."
                    ),
                    "player_qualified_id",
                    qualified_id=player_qualified_id,
                )
            )
    if not world_objects:
        issues.append(
            _issue(
                ClassroomTrailPlanIssueCode.WORLD_OBJECT_REQUIRED,
                "A Classroom Trail requires at least one world object.",
                "selections",
            )
        )
    if issues:
        return ClassroomTrailPlanResult(None, tuple(issues))

    assert player is not None
    return ClassroomTrailPlanResult(
        ClassroomTrailPlan(
            contract_version=SUPPORTED_CLASSROOM_TRAIL_CONTRACT_VERSION,
            packages=tuple(sorted(packages, key=lambda package: package.package_id)),
            player=player,
            npcs=tuple(character for character in characters if character != player),
            world_objects=world_objects,
        ),
        (),
    )


def plan_local_classroom_trail(
    package_roots: Iterable[str | Path],
    *,
    player_qualified_id: str | None = None,
) -> ClassroomTrailPlanResult:
    """Load independent local package roots and plan them as one trail."""
    selections: list[PackageSelection] = []
    for root in package_roots:
        loaded = load_explorer_package(root)
        registration = plan_loaded_explorer_package(loaded)
        if registration.plan is None:
            return ClassroomTrailPlanResult(
                None,
                (
                    _issue(
                        ClassroomTrailPlanIssueCode.PACKAGE_INVALID,
                        "A local package could not be loaded and planned declaratively.",
                        "package_roots",
                    ),
                ),
            )
        provenance = registration.plan.provenance
        selections.append(
            PackageSelection(
                package_id=provenance.package_id,
                package_version=provenance.package_version,
                registration_plan=registration.plan,
            )
        )
    return build_classroom_trail_plan(
        selections,
        player_qualified_id=player_qualified_id,
    )


def create_classroom_trail_scene(
    renderer: object,
    plan: ClassroomTrailPlan,
    *,
    mission_id: str = DEFAULT_CLASSROOM_TRAIL_MISSION_ID,
) -> ClassroomTrailScene:
    """Translate one immutable trail plan into engine-owned runtime objects."""
    from engine.entities import Character as EngineCharacter
    from engine.entities import WorldObject as EngineWorldObject
    from engine.scenes import (
        ClassroomTrailNPC,
        ClassroomTrailObject,
        ClassroomTrailObjectToggle,
        ClassroomTrailScene,
    )
    from explore.curriculum import get_course_mission

    if not isinstance(plan, ClassroomTrailPlan):
        raise TypeError("plan must be a ClassroomTrailPlan")
    if plan.contract_version != SUPPORTED_CLASSROOM_TRAIL_CONTRACT_VERSION:
        raise ValueError('plan.contract_version must be "0.5"')
    mission = get_course_mission(mission_id)
    if (
        not isinstance(plan.packages, tuple)
        or not plan.packages
        or any(type(package) is not SelectedPackagePlan for package in plan.packages)
    ):
        raise ValueError("plan.packages must contain canonical selected package plans")
    if tuple(package.package_id for package in plan.packages) != tuple(
        sorted(package.package_id for package in plan.packages)
    ):
        raise ValueError("plan.packages must be ordered by package ID")
    canonical_entries = tuple(
        entry for package in plan.packages for entry in package.registration_plan.entries
    )
    canonical_characters = tuple(
        sorted(
            (entry for entry in canonical_entries if type(entry) is CharacterRegistration),
            key=lambda entry: entry.qualified_id,
        )
    )
    canonical_objects = tuple(
        sorted(
            (entry for entry in canonical_entries if type(entry) is WorldObjectRegistration),
            key=lambda entry: entry.qualified_id,
        )
    )
    canonical_player = tuple(
        entry for entry in canonical_characters if entry.qualified_id == plan.player.qualified_id
    )
    canonical_npcs = tuple(entry for entry in canonical_characters if entry != plan.player)
    if (
        canonical_player != (plan.player,)
        or canonical_npcs != plan.npcs
        or canonical_objects != plan.world_objects
    ):
        raise ValueError("plan must retain its canonical package contribution projection")
    player = plan.player.character
    engine_player = EngineCharacter(
        name=player.name,
        x=player.x,
        y=player.y,
        width=100,
        height=100,
        color=resolve_color(player.color),
    )
    engine_objects = tuple(
        ClassroomTrailObject(
            qualified_id=entry.qualified_id,
            world_object=EngineWorldObject(
                name=entry.world_object.name,
                x=entry.world_object.x,
                y=entry.world_object.y,
                width=80,
                height=60,
                color=resolve_color(entry.world_object.color),
            ),
            when_near=entry.world_object.when_near,
            when_interacted=entry.world_object.when_interacted,
            toggle=(
                None
                if entry.world_object.toggle is None
                else ClassroomTrailObjectToggle(
                    off_color=resolve_color(entry.world_object.toggle.off_color),
                    on_color=resolve_color(entry.world_object.toggle.on_color),
                )
            ),
        )
        for entry in plan.world_objects
    )
    engine_npcs = tuple(
        ClassroomTrailNPC(
            qualified_id=entry.qualified_id,
            character=EngineCharacter(
                name=entry.character.name,
                x=entry.character.x,
                y=entry.character.y,
                width=100,
                height=100,
                color=resolve_color(entry.character.color),
            ),
            greeting=entry.character.greeting,
            conversation=entry.character.conversation,
        )
        for entry in plan.npcs
    )
    return ClassroomTrailScene(  # type: ignore[arg-type]
        renderer,
        engine_player,
        engine_objects,
        engine_npcs,
        mission=mission,
    )


def run_classroom_trail(
    plan: ClassroomTrailPlan,
    *,
    name: str = "Classroom Trail",
    mission_id: str = DEFAULT_CLASSROOM_TRAIL_MISSION_ID,
) -> None:
    """Run one planned trail locally until the window is closed."""
    from engine._config import Config
    from engine._platform import Platform
    from engine.input import InteractionInput
    from engine.rendering import Renderer
    from explore.curriculum import get_course_mission

    get_course_mission(mission_id)
    config = Config(app_name=name)
    platform = Platform(config)
    platform.initialize()
    scene: ClassroomTrailScene | None = None
    try:
        renderer = Renderer(platform)
        scene = create_classroom_trail_scene(renderer, plan, mission_id=mission_id)
        scene.enter()
        while True:
            events = platform.poll_frame_events()
            if events.quit_requested:
                break
            dt = platform.tick()
            directional_input = platform.poll_directional_input()
            scene.update(
                directional_input,
                InteractionInput(interact_pressed=events.interaction_pressed),
                dt,
            )
            renderer.clear_frame(config.background_color)
            scene.render()
            renderer.present_frame()
    finally:
        if scene is not None:
            scene.exit()
        platform.shutdown()
