"""Late-session polish observes existing gameplay and keeps publication at S09."""

import shutil

import pytest
import yaml

from engine.rendering._mission_presentation import COURSE_TRAIL_PROFILES, mission_presentation
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from scripts.capture_remaining_trails import ROOT, exercise, interact
from scripts.trail_driver import Trail
from tests.test_mission_presentation_contract import AccentCheckingRenderer


@pytest.mark.parametrize("session", COURSE_TRAIL_PROFILES)
def test_every_later_reference_completes_without_presentation_failures(session):
    assert exercise(session)["complete"]


@pytest.mark.parametrize(
    "session,mission",
    [
        ("S18", "count-object-interactions"),
        ("S23", "respond-to-object-state"),
        ("S27", "reuse-a-named-toggle-style"),
        ("S28", "complete-actions-in-order"),
        ("S29", "complete-actions-in-order"),
        ("S30", "complete-actions-in-order"),
        ("S30", "reuse-a-named-toggle-style"),
    ],
)
def test_composed_mechanics_keep_distinct_completion_contracts(session, mission):
    assert exercise(session, mission=mission)["complete"]


def test_student_owned_package_and_object_ids_can_change(tmp_path):
    root = tmp_path / "my-package"
    shutil.copytree(ROOT / "lessons/sessions/s23/student/explorer-package", root)
    path = root / "manifest.yaml"
    data = yaml.safe_load(path.read_text())
    data["package"]["id"] = "my-original-world"
    replacements = {
        "design-lamp": "my-first-lamp",
        "build-lamp": "my-second-lamp",
        "workshop-keeper": "my-friend",
    }
    for contribution in data["contributions"]:
        contribution["id"] = replacements[contribution["id"]]
    path.write_text(yaml.safe_dump(data))
    keeper = root / "character/workshop-keeper.yaml"
    record = yaml.safe_load(keeper.read_text())
    record["respond_to_toggle"]["object_id"] = "my-first-lamp"
    keeper.write_text(yaml.safe_dump(record))
    # Neither a course package id nor any course object name is needed.
    for file in (root / "objects").glob("*.yaml"):
        item = yaml.safe_load(file.read_text())
        item["name"] = "My own lamp"
        file.write_text(yaml.safe_dump(item))
    assert exercise("S23", package=root, presentation_session="S23")["complete"]
    assert (
        mission_presentation("reuse-a-named-toggle-style", package_ids=("my-original-world",))
        is None
    )


def test_profile_is_explicit_and_cannot_change_the_selected_mission():
    assert "S26" not in COURSE_TRAIL_PROFILES
    assert mission_presentation(None) is None
    for sid, (_, missions, _) in COURSE_TRAIL_PROFILES.items():
        assert mission_presentation(missions[0], package_ids=("unrelated-package",)) is None
        assert mission_presentation(missions[0], presentation_session=sid).authored_roles
        with pytest.raises(ValueError, match="does not support"):
            mission_presentation("visit-all-classroom-objects", presentation_session=sid)
    with pytest.raises(ValueError, match="unknown"):
        mission_presentation("complete-actions-in-order", presentation_session="S26")
    roots = (
        ROOT / "examples/explorer-packages/nova-character",
        ROOT / "lessons/sessions/s23/student/explorer-package",
    )
    planned = plan_local_classroom_trail(roots, player_qualified_id="nova-character:nova")
    with pytest.raises(ValueError, match="explicit mission"):
        create_classroom_trail_scene(
            AccentCheckingRenderer(), planned.plan, presentation_session="S23"
        )


def test_s18_devices_have_independent_authored_goal_cells():
    trail = Trail(
        (
            ROOT / "examples/explorer-packages/nova-character",
            ROOT / "lessons/sessions/s18/student/explorer-package",
        ),
        mission_id="count-object-interactions",
    )
    try:
        trail.hold(0.2)
        for item in trail.scene.objects:
            for other in trail.scene.objects:
                if other != item:
                    assert trail.scene.counter_counts[other.qualified_id] in (0, other.counter.goal)
            interact(trail, item.qualified_id)
            assert trail.scene._presentation.pose_for(item.qualified_id).column == "lit-1"
            for _ in range(item.counter.goal - 1):
                interact(trail, item.qualified_id)
            assert (
                trail.scene._presentation.pose_for(item.qualified_id).column
                == f"lit-{item.counter.goal}"
            )
            for other in trail.scene.objects:
                if other != item and trail.scene.counter_counts[other.qualified_id] == 0:
                    assert trail.scene._presentation.pose_for(other.qualified_id).column == "lit-0"
        assert trail.scene.mission_is_complete
    finally:
        trail.close()


def test_s15_cells_follow_reset_without_replaying_or_mutating_sequence():
    trail = Trail(
        (
            ROOT / "examples/explorer-packages/nova-character",
            ROOT / "lessons/sessions/s15/student/explorer-package",
        ),
        mission_id="complete-actions-in-order",
    )
    try:
        npc = trail.scene.npcs[0]
        ids = npc.respond_to_sequence.object_qualified_ids
        interact(trail, ids[0])
        assert trail.scene._presentation._sequence_counts[npc.qualified_id] == 1
        interact(trail, ids[0])
        assert trail.scene._presentation._sequence_counts[npc.qualified_id] == 0
        for q in ids:
            interact(trail, q)
        assert trail.scene._presentation._sequence_counts[npc.qualified_id] == 3
        assert trail.scene.mission_is_complete
        # The drum counter's goal is separate from the ordered-route rule.
        drum = next(o for o in trail.scene.objects if o.counter)
        assert trail.scene.counter_counts[drum.qualified_id] == 1 < drum.counter.goal
    finally:
        trail.close()


def test_all_notes_keep_student_tasks_and_no_planning_trail():
    for number in range(10, 31):
        student = ROOT / f"lessons/sessions/s{number:02}/student"
        notes = (student / "python-notes.md").read_text()
        assert "## 7." in notes and "Local Python" in notes
        if number == 26:
            assert not (student / "explorer-package").exists()
            assert not (student / "trail-checkpoints.md").exists()
        else:
            guide = (student / "trail-checkpoints.md").read_text()
            assert f"--presentation-session S{number:02}" in guide
            assert "not a general assessment" in guide


def test_cli_passes_the_profile_and_rejects_mismatches(monkeypatch, capsys):
    from explore.packages import cli

    calls = []
    monkeypatch.setattr(cli, "run_classroom_trail", lambda plan, **options: calls.append(options))
    args = [
        "trail",
        str(ROOT / "examples/explorer-packages/nova-character"),
        str(ROOT / "lessons/sessions/s23/student/explorer-package"),
        "--player",
        "nova-character:nova",
        "--mission-id",
        "reuse-a-named-toggle-style",
        "--presentation-session",
        "S23",
    ]
    assert cli.main(args) == 0
    assert calls[-1]["presentation_session"] == "S23"
    assert calls[-1]["mission_id"] == "reuse-a-named-toggle-style"
    args[-1] = "S10"
    assert cli.main(args) == 1
    assert "does not support" in capsys.readouterr().out
    assert len(calls) == 1
