from __future__ import annotations

import ast
import runpy
from pathlib import Path

import yaml

from explore.curriculum.missions import MISSION_15_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
S25_ROOT = MATERIALS_ROOT / "s25"
STUDENT_ROOT = S25_ROOT / "student"
STUDENT_PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
RECOVERY_PACKAGE_ROOT = STUDENT_ROOT / "recovery-package"


def test_s25_v2_identity_classification_and_exact_rhythm():
    runbook = (S25_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")

    assert runbook.startswith("# S25 — Playable Prototype")
    assert task.startswith("# S25 Task Card — Playable Prototype")
    assert "**Role:** Project-primary production lesson" in runbook
    assert "**Role:** Project-primary production lesson" in task
    assert all(
        anchor in runbook
        for anchor in (
            "0:00–0:04",
            "0:04–0:09",
            "0:09–0:31",
            "0:31–0:38",
            "0:38–0:42",
            "0:42–0:45",
        )
    )
    assert (STUDENT_ROOT / "starter.py").is_file()
    assert (STUDENT_ROOT / "fixtures.py").is_file()
    assert (STUDENT_ROOT / "test_pipeline.py").is_file()
    assert (STUDENT_ROOT / "project-record.md").is_file()
    assert (STUDENT_ROOT / "project_catalog.py").is_file()
    assert (STUDENT_PACKAGE_ROOT / "manifest.yaml").is_file()
    assert (RECOVERY_PACKAGE_ROOT / "manifest.yaml").is_file()
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(31, 32))


def test_s25_starter_runs_but_leaves_four_core_functions_incomplete(capsys):
    source = (STUDENT_ROOT / "starter.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

    assert all(
        name in functions
        for name in ("validate_station", "select_route", "signal_total", "ordered_route")
    )
    for name in ("validate_station", "select_route", "signal_total", "ordered_route"):
        function_source = ast.get_source_segment(source, functions[name])
        assert function_source is not None and "TODO" in function_source
    runpy.run_path(str(STUDENT_ROOT / "starter.py"), run_name="__main__")
    assert "S25 scaffold ready" in capsys.readouterr().out


def test_s25_requires_three_core_criteria_with_four_and_five_optional():
    runbook = (S25_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    record = (STUDENT_ROOT / "project-record.md").read_text(encoding="utf-8")
    normalized = " ".join(task.lower().split())

    assert "exactly 3 core observable acceptance criteria" in normalized
    assert "criteria 4–5 are optional extensions" in normalized
    assert "premise before class" in normalized
    assert task.count("| ___ |") >= 4
    assert all(
        phrase in normalized
        for phrase in (
            "visitor path",
            "invalid-data path",
            "selected ids",
            "expected total `signal_power`",
        )
    )
    criteria = runbook.split("## Acceptance-criteria calibration", 1)[1].split("##", 1)[0]
    assert (
        sum(line.startswith(("1. Core:", "2. Core:", "3. Core:")) for line in criteria.splitlines())
        == 3
    )
    assert (
        sum(
            line.startswith(("4. Optional extension:", "5. Optional extension:"))
            for line in criteria.splitlines()
        )
        == 2
    )
    assert all(f"{number}. Core:" in record for number in range(1, 4))
    assert "4. Optional extension:" in record and "5. Optional extension:" in record
    assert "choose your own" in normalized


def test_s25_pipeline_and_five_case_learning_tests_are_explicit():
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    starter = (STUDENT_ROOT / "starter.py").read_text(encoding="utf-8")
    tests = (STUDENT_ROOT / "test_pipeline.py").read_text(encoding="utf-8")

    assert (
        "validate → filter enabled → search required IDs → count selected\n"
        "→ aggregate signal power → stable sort → transform preview"
    ) in task
    assert "sorted(..., key=...)" in starter
    assert all(
        name in tests
        for name in (
            "test_normal_valid_catalog",
            "test_exactly_three_boundary",
            "test_absent_required_id_fails_closed_before_preview",
            "test_malformed_coordinate_type_fails_closed_before_preview",
            "test_stable_order_regression",
        )
    )
    assert tests.count("assert not preview_called") == 2
    assert "STABLE_REQUIRED_IDS" in tests
    expected = "These tests are expected to fail until you complete the TODO functions."
    assert task.count(expected) == 1
    assert task.index(expected) < task.index(
        "python -m pytest -q lessons/sessions/s25/student/test_pipeline.py"
    )


def test_s25_fixtures_cover_nested_normal_boundary_absent_malformed_and_stability():
    fixtures = runpy.run_path(str(STUDENT_ROOT / "fixtures.py"))
    normal = fixtures["NORMAL_CATALOG"]
    boundary = fixtures["EXACTLY_THREE_CATALOG"]
    absent = fixtures["ABSENT_REQUIRED_CATALOG"]
    malformed = fixtures["MALFORMED_COORDINATE_CATALOG"]
    regression = fixtures["STABLE_ORDER_CATALOG"]

    assert len(normal["regions"]) == 2
    assert sum(len(region["stations"]) for region in normal["regions"]) == 5
    assert len(boundary["regions"][0]["stations"]) == 3
    enabled = [
        station
        for region in normal["regions"]
        for station in region["stations"]
        if station["enabled"]
    ]
    required = {"harbor-drum", "north-lantern", "summit-flare"}
    selected = [station for station in enabled if station["id"] in required]
    assert len(selected) == 3
    assert sum(station["signal_power"] for station in selected) == 12
    ordered = sorted(selected, key=lambda item: item["route_order"])
    assert [station["id"] for station in ordered] == [
        "harbor-drum",
        "north-lantern",
        "summit-flare",
    ]
    assert "summit-flare" not in {
        station["id"] for region in absent["regions"] for station in region["stations"]
    }
    assert malformed["regions"][0]["stations"][0]["world"]["x"] == "410"
    orders = [station["route_order"] for station in regression["regions"][0]["stations"]]
    assert orders == [1, 1, 2]


def test_s25_recovery_package_validates_plans_and_uses_exact_m15_sequence():
    loaded = load_explorer_package(RECOVERY_PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (
            PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character",
            RECOVERY_PACKAGE_ROOT,
        ),
        player_qualified_id="nova-character:nova",
    )
    manifest = yaml.safe_load((RECOVERY_PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    keeper = yaml.safe_load(
        (RECOVERY_PACKAGE_ROOT / "character" / "rescue-keeper.yaml").read_text(encoding="utf-8")
    )

    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    world_contributions = [
        item for item in manifest["contributions"] if item["type"] == "world_object"
    ]
    assert len(world_contributions) == 3
    assert keeper["respond_to_sequence"]["object_ids"] == [
        "harbor-drum",
        "north-lantern",
        "summit-flare",
    ]

    scene = create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_15_ID)
    guide_id = "stormlight-rescue-trail:rescue-keeper"
    scene._update_sequence_progress("stormlight-rescue-trail:harbor-drum")
    scene._update_sequence_progress("stormlight-rescue-trail:summit-flare")
    assert scene.sequence_progress[guide_id] == 0
    assert not scene.mission_is_complete
    for object_id in ("harbor-drum", "north-lantern", "summit-flare"):
        scene._update_sequence_progress(f"stormlight-rescue-trail:{object_id}")
    assert scene.sequence_progress[guide_id] == 3
    assert scene.mission_is_complete

    boundary = " ".join(
        (
            (S25_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
            + (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
        )
        .lower()
        .split()
    )
    assert "teacher-only" in boundary
    assert "partial recovery" in boundary
    assert "does not complete" in boundary
    assert "later finish" in boundary
    assert "every prediction" in boundary
    assert "at least one completed function" in boundary


def test_s25_ai_git_self_review_support_and_runtime_boundaries_are_explicit():
    runbook = (S25_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join(task.lower().split())

    assert "one bounded scope-critique question only" in normalized
    assert all(
        forbidden in normalized
        for forbidden in (
            "premise",
            "acceptance criteria",
            "pipeline",
            "function bodies",
            "route solution",
            "test answers",
        )
    )
    assert "do not paste whole files or ask ai for a complete solution." in normalized
    assert all(
        field in normalized
        for field in (
            "intent",
            "prediction",
            "exact bounded question",
            "suggestion tested",
            "accepted/rejected change",
            "student explanation",
        )
    )
    assert all(
        phrase in task
        for phrase in (
            "Creative choice I own",
            "Python change I can explain",
            "Test run and result",
            "deliberately deferred",
            "prepared three-record",
            "text-only",
        )
    )
    assert "Planning and prototype implementation belong in separate commits" in task
    assert "git status --short" in task and "git diff --staged" in task
    assert all(item in normalized for item in ("`m`", "`??`", "no output", "identity"))
    assert "python remains local" in normalized
    assert "local python helps you reason, transform, and validate" in normalized
    assert "validated package yaml drives the visible world" in normalized
    assert "shared runtime never executes student python" in normalized
    assert "do not add fields to the runtime schema" in normalized
    assert "do not add a fourth sequence member" in normalized
    assert "no python, catalog-only fields, or new behavior enters\nthe runtime" in runbook.lower()


def test_s25_editable_project_catalog_is_student_owned_and_differs_from_fixtures():
    project_source = (STUDENT_ROOT / "project_catalog.py").read_text(encoding="utf-8")
    fixture_source = (STUDENT_ROOT / "fixtures.py").read_text(encoding="utf-8")
    project = runpy.run_path(str(STUDENT_ROOT / "project_catalog.py"))
    fixtures = runpy.run_path(str(STUDENT_ROOT / "fixtures.py"))

    stations = project["PROJECT_CATALOG"]["regions"][0]["stations"]
    assert len(stations) == 3
    assert tuple(station["id"] for station in stations) == project["PROJECT_ROUTE_IDS"]
    assert project["PROJECT_CATALOG"] != fixtures["NORMAL_CATALOG"]
    assert "My editable S25 project source" in project_source
    assert "Safe bounds" in project_source
    assert "Students should not edit these test fixtures" in fixture_source
    assert all(
        set(station)
        == {
            "id",
            "name",
            "enabled",
            "route_order",
            "signal_power",
            "world",
        }
        for station in stations
    )


def test_s25_student_package_validates_plans_and_plays_existing_m15():
    loaded = load_explorer_package(STUDENT_PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (
            PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character",
            STUDENT_PACKAGE_ROOT,
        ),
        player_qualified_id="nova-character:nova",
    )
    manifest = yaml.safe_load((STUDENT_PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    keeper = yaml.safe_load(
        (STUDENT_PACKAGE_ROOT / "character" / "garden-keeper.yaml").read_text(encoding="utf-8")
    )

    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    objects = [item for item in manifest["contributions"] if item["type"] == "world_object"]
    assert len(objects) == 3
    route_ids = ["seed-marker", "brook-chime", "moon-bloom"]
    assert keeper["respond_to_sequence"]["object_ids"] == route_ids

    scene = create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_15_ID)
    for object_id in route_ids:
        scene._update_sequence_progress(f"moonlit-garden-route:{object_id}")
    assert scene.mission_is_complete


def test_s25_student_package_is_materially_distinct_and_mapping_is_complete():
    student_manifest = yaml.safe_load(
        (STUDENT_PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8")
    )
    recovery_manifest = yaml.safe_load(
        (RECOVERY_PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8")
    )
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")

    assert student_manifest["package"]["id"] != recovery_manifest["package"]["id"]
    assert (
        student_manifest["package"]["display_name"] != recovery_manifest["package"]["display_name"]
    )
    student_ids = {item["id"] for item in student_manifest["contributions"]}
    recovery_ids = {item["id"] for item in recovery_manifest["contributions"]}
    assert student_ids.isdisjoint(recovery_ids)
    assert all(
        phrase in task
        for phrase in (
            "station `id`",
            "station `name` and story text",
            "`world.x` and `world.y`",
            "`world.color`",
            "`route_order`",
            "`when_near`",
            "`when_interacted`",
            "`respond_to_sequence.object_ids`",
            "`signal_power`",
        )
    )
