"""Focused tests for the additive local Classroom Trail contract."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from engine.entities import Character, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.scenes import ClassroomTrailObject, ClassroomTrailScene
from explore.packages import (
    ClassroomTrailPlan,
    ClassroomTrailPlanIssueCode,
    PackageSelection,
    build_classroom_trail_plan,
    build_package_set_plan,
    create_classroom_trail_scene,
    export_explorer_package,
    load_explorer_package,
    plan_loaded_explorer_package,
    plan_local_classroom_trail,
)

_NO_MOVEMENT = DirectionalInput()
_NO_INTERACTION = InteractionInput()
_INTERACT = InteractionInput(interact_pressed=True)


class _RecordingRenderer:
    def __init__(self) -> None:
        self.rectangles: list[tuple[object, ...]] = []
        self.text: list[str] = []

    def draw_rect(self, *values: object) -> None:
        self.rectangles.append(values)

    def draw_text(self, text: str, *values: object) -> None:
        self.text.append(text)


def _trail_object(
    qualified_id: str,
    x: int,
    *,
    near: str | None = None,
    interacted: str | None = None,
) -> ClassroomTrailObject:
    return ClassroomTrailObject(
        qualified_id,
        WorldObject(
            name=qualified_id,
            x=x,
            y=0,
            width=20,
            height=20,
            color=(0, 255, 0),
        ),
        near,
        interacted,
    )


def _scene(*objects: ClassroomTrailObject, interaction_range: int = 120) -> ClassroomTrailScene:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(
            name="Player",
            x=0,
            y=0,
            width=20,
            height=20,
            color=(255, 200, 50),
        ),
        tuple(objects),
        interaction_range=interaction_range,
    )
    scene.enter()
    return scene


def _write_package(
    root: Path,
    package_id: str,
    contribution_id: str,
    contribution_type: str,
    body: str,
) -> Path:
    contribution_dir = "character" if contribution_type == "character" else "objects"
    contribution_path = f"{contribution_dir}/{contribution_id}.yaml"
    root.mkdir()
    (root / contribution_dir).mkdir()
    (root / "manifest.yaml").write_text(
        (
            'schema_version: "0.1"\n'
            "package:\n"
            f'  id: "{package_id}"\n'
            f'  display_name: "{package_id}"\n'
            '  version: "1.0.0"\n'
            "compatibility:\n"
            '  student_api: "0.1"\n'
            "contributions:\n"
            f'  - id: "{contribution_id}"\n'
            f'    type: "{contribution_type}"\n'
            f'    path: "{contribution_path}"\n'
        ),
        encoding="utf-8",
    )
    (root / contribution_path).write_text(body, encoding="utf-8")
    return root


def _selection(root: Path) -> PackageSelection:
    registration = plan_loaded_explorer_package(load_explorer_package(root))
    assert registration.plan is not None
    provenance = registration.plan.provenance
    return PackageSelection(
        provenance.package_id,
        provenance.package_version,
        registration.plan,
    )


def test_nearest_in_range_object_is_targeted() -> None:
    scene = _scene(
        _trail_object("far:object", 80),
        _trail_object("near:object", 30),
    )

    scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)

    assert scene.target_qualified_id == "near:object"


def test_equal_distance_tie_uses_qualified_id() -> None:
    scene = _scene(
        _trail_object("zebra:object", 40),
        _trail_object("alpha:object", 40),
    )

    scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)

    assert scene.target_qualified_id == "alpha:object"


def test_only_in_range_interactions_change_session_state() -> None:
    scene = _scene(_trail_object("far:object", 300), interaction_range=50)

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert scene.did_interact_this_frame is False
    assert scene.visited_qualified_ids == frozenset()
    assert scene.is_complete is False


def test_visited_identity_is_idempotent_and_all_objects_complete_trail() -> None:
    scene = _scene(
        _trail_object("alpha:object", 30),
        _trail_object("beta:object", 260),
        interaction_range=80,
    )

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.visited_qualified_ids == frozenset({"alpha:object"})
    assert scene.is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.5)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert scene.visited_qualified_ids == frozenset({"alpha:object", "beta:object"})
    assert scene.is_complete is True


def test_ui_shows_authored_messages_progress_and_completion() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(
            name="Player",
            x=0,
            y=0,
            width=20,
            height=20,
            color=(255, 200, 50),
        ),
        (
            _trail_object(
                "student:lantern",
                30,
                near="The lantern glows.",
                interacted="A crystal spark appears!",
            ),
        ),
    )
    scene.enter()
    scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)
    scene.render()
    assert "Visited 0 / 1" in renderer.text
    assert "The lantern glows." in renderer.text

    renderer.text.clear()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Visited 1 / 1" in renderer.text
    assert "Trail complete!" in renderer.text
    assert "A crystal spark appears!" in renderer.text


def test_v01_rejects_but_v02_trail_accepts_multiple_package_objects(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
    )
    alpha_root = _write_package(
        tmp_path / "alpha",
        "alpha-package",
        "lantern",
        "world_object",
        (
            'name: "Lantern"\nx: 30\ny: 0\ncolor: "yellow"\n'
            'when_near: "The lantern glows."\n'
            'when_interacted: "A spark appears!"\n'
        ),
    )
    beta_root = _write_package(
        tmp_path / "beta",
        "beta-package",
        "fountain",
        "world_object",
        (
            'name: "Fountain"\nx: 260\ny: 0\ncolor: "blue"\n'
            'when_near: "Water hums."\n'
            'when_interacted: "You found a ripple!"\n'
        ),
    )
    selections = tuple(_selection(root) for root in (player_root, alpha_root, beta_root))

    assert build_package_set_plan(selections).is_planned is False
    trail = build_classroom_trail_plan(selections)

    assert trail.is_planned
    assert trail.plan is not None
    assert trail.plan.contract_version == "0.2"
    assert [item.qualified_id for item in trail.plan.world_objects] == [
        "alpha-package:lantern",
        "beta-package:fountain",
    ]


def test_v02_accepts_multiple_objects_from_one_package(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\n',
    )
    object_root = _write_package(
        tmp_path / "objects",
        "shared-package",
        "lantern",
        "world_object",
        'name: "Lantern"\nx: 30\ny: 0\n',
    )
    manifest = object_root / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8")
        + (
            '  - id: "fountain"\n'
            '    type: "world_object"\n'
            '    path: "objects/fountain.yaml"\n'
        ),
        encoding="utf-8",
    )
    (object_root / "objects" / "fountain.yaml").write_text(
        'name: "Fountain"\nx: 260\ny: 0\n',
        encoding="utf-8",
    )
    selections = (_selection(player_root), _selection(object_root))

    assert build_package_set_plan(selections).is_planned is False
    result = build_classroom_trail_plan(selections)

    assert result.plan is not None
    assert [item.qualified_id for item in result.plan.world_objects] == [
        "shared-package:fountain",
        "shared-package:lantern",
    ]


def test_multiple_local_exports_feed_one_runnable_trail_plan(tmp_path: Path) -> None:
    roots = (
        _write_package(
            tmp_path / "player",
            "player-package",
            "player",
            "character",
            'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
        ),
        _write_package(
            tmp_path / "alpha",
            "alpha-package",
            "lantern",
            "world_object",
            'name: "Lantern"\nx: 30\ny: 0\ncolor: "yellow"\n',
        ),
        _write_package(
            tmp_path / "beta",
            "beta-package",
            "fountain",
            "world_object",
            'name: "Fountain"\nx: 260\ny: 0\ncolor: "blue"\n',
        ),
    )
    export_root = tmp_path / "exports"
    export_root.mkdir()
    for root in roots:
        loaded = load_explorer_package(root)
        assert loaded.package is not None
        destination = export_root / (f"{loaded.package.metadata.id}-1.0.0.explorer-package.zip")
        assert export_explorer_package(root, destination).is_exported

    planned = plan_local_classroom_trail(reversed(roots))
    assert planned.is_planned
    assert planned.plan is not None
    assert [package.package_id for package in planned.plan.packages] == [
        "alpha-package",
        "beta-package",
        "player-package",
    ]

    scene = create_classroom_trail_scene(_RecordingRenderer(), planned.plan)
    assert scene.player.name == "Player"
    assert [item.qualified_id for item in scene.objects] == [
        "alpha-package:lantern",
        "beta-package:fountain",
    ]


def test_trail_requires_exactly_one_player(tmp_path: Path) -> None:
    first = _write_package(
        tmp_path / "first",
        "first-player",
        "player",
        "character",
        'name: "First"\n',
    )
    second = _write_package(
        tmp_path / "second",
        "second-player",
        "player",
        "character",
        'name: "Second"\n',
    )
    object_root = _write_package(
        tmp_path / "object",
        "object-package",
        "object",
        "world_object",
        'name: "Object"\nx: 10\ny: 10\n',
    )

    result = build_classroom_trail_plan(
        (_selection(first), _selection(second), _selection(object_root))
    )

    assert result.plan is None
    assert [issue.code for issue in result.issues] == [
        ClassroomTrailPlanIssueCode.PLAYER_CARDINALITY_EXCEEDED
    ]


def test_cli_runs_planned_local_trail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\n',
    )
    object_root = _write_package(
        tmp_path / "object",
        "object-package",
        "object",
        "world_object",
        'name: "Object"\nx: 10\ny: 10\n',
    )
    calls: list[tuple[str, int]] = []

    from explore.packages import cli

    def record_run(plan: ClassroomTrailPlan, *, name: str) -> None:
        calls.append((name, len(plan.world_objects)))

    monkeypatch.setattr(cli, "run_classroom_trail", record_run)

    assert (
        cli.main(
            [
                "trail",
                str(object_root),
                str(player_root),
                "--name",
                "Room 12 Trail",
            ]
        )
        == 0
    )
    assert calls == [("Room 12 Trail", 1)]


def test_runtime_rejects_changed_contract_version(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\n',
    )
    object_root = _write_package(
        tmp_path / "object",
        "object-package",
        "object",
        "world_object",
        'name: "Object"\nx: 10\ny: 10\n',
    )
    result = plan_local_classroom_trail((player_root, object_root))
    assert result.plan is not None

    changed = replace(result.plan, contract_version="9.9")

    with pytest.raises(ValueError, match="contract_version"):
        create_classroom_trail_scene(_RecordingRenderer(), changed)
