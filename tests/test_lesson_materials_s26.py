from __future__ import annotations

import ast
import importlib.util
import runpy
import subprocess
import sys
from pathlib import Path

import yaml

from engine.input import DirectionalInput, InteractionInput
from explore.curriculum.missions import MISSION_03_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
S26_ROOT = MATERIALS_ROOT / "s26"
STUDENT_ROOT = S26_ROOT / "student"
STUDENT_PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
RECOVERY_PACKAGE_ROOT = S26_ROOT / "teacher-recovery-package"
LEARNER_TEST = STUDENT_ROOT / "test_blueprint.py"


def test_s26_identity_classification_structure_and_exact_rhythm():
    runbook = (S26_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")

    assert runbook.startswith("# S26 — Capstone Blueprint")
    assert task.startswith("# S26 Task Card — Capstone Blueprint")
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
    assert all(
        (STUDENT_ROOT / name).is_file()
        for name in (
            "task-card.md",
            "project-record.md",
            "project_data.py",
            "starter.py",
            "fixtures.py",
            "test_blueprint.py",
        )
    )
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(30, 31))


def test_s26_project_record_persists_scope_evidence_and_decisions():
    record = (STUDENT_ROOT / "project-record.md").read_text(encoding="utf-8")

    assert record.startswith("# My S26 Project Record")
    assert all(
        heading in record
        for heading in (
            "## Premise",
            "## Acceptance criteria",
            "## Data-flow prediction",
            "## Responsibility map",
            "## Function contracts",
            "## Scope, risks, and decisions",
            "## Test and playable evidence",
            "## Milestone self-review",
            "## AI criterion-review receipt",
        )
    )
    assert all(f"{number}. Core:" in record for number in range(1, 4))
    assert "Known risk 1" in record
    assert "Known risk 2" in record
    assert "One decision deliberately deferred" in record
    assert "never becomes runtime metadata" in record


def test_s26_requires_student_created_responsibility_map_and_three_contracts():
    runbook = (S26_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    record = (STUDENT_ROOT / "project-record.md").read_text(encoding="utf-8")
    normalized = " ".join((runbook + task).lower().split())

    assert "at least three function contracts" in normalized
    assert record.count("### Contract ") >= 3
    assert all(
        field in record
        for field in (
            "Function name",
            "Inputs",
            "Return shape",
            "Expected error/failure behavior",
            "Side effects, if any",
            "One concrete example",
        )
    )
    assert all(
        responsibility in record
        for responsibility in (
            "Data input",
            "Validation",
            "Selection/rules",
            "Transformation",
            "Package build/output",
            "Validation/play",
            "Tests",
        )
    )
    assert "i create this map" in record.lower()
    assert "validation separate from file i/o" in normalized
    assert "pure rule functions file-free" in normalized


def test_s26_editable_nested_data_is_distinct_from_fixed_fixtures():
    project_source = (STUDENT_ROOT / "project_data.py").read_text(encoding="utf-8")
    fixture_source = (STUDENT_ROOT / "fixtures.py").read_text(encoding="utf-8")
    project = runpy.run_path(str(STUDENT_ROOT / "project_data.py"))
    fixtures = runpy.run_path(str(STUDENT_ROOT / "fixtures.py"))
    expedition = project["PROJECT_EXPEDITION"]

    assert "My editable S26 capstone source" in project_source
    assert "Students should not edit this file" in fixture_source
    assert isinstance(expedition["zones"], list)
    assert len(expedition["zones"]) >= 2
    assert all(isinstance(zone["stations"], list) for zone in expedition["zones"])
    station = expedition["zones"][0]["stations"][0]
    assert set(station) == {
        "id",
        "name",
        "enabled",
        "coordinates",
        "color",
        "route_order",
        "signal_power",
        "story",
    }
    assert set(station["coordinates"]) == {"x", "y"}
    assert set(station["story"]) == {"when_near", "when_interacted"}
    assert expedition != fixtures["MINIMAL_VALID_EXPEDITION"]


def test_s26_scaffold_runs_and_keeps_contract_todos_incomplete(capsys):
    source = (STUDENT_ROOT / "starter.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    core = (
        "validate_station",
        "flatten_stations",
        "validate_expedition",
        "select_stations",
        "build_package_preview",
    )

    assert all(name in functions for name in core)
    for name in core:
        function_source = ast.get_source_segment(source, functions[name])
        assert function_source is not None and "TODO contract" in function_source
    runpy.run_path(str(STUDENT_ROOT / "starter.py"), run_name="__main__")
    assert "S26 blueprint scaffold ready" in capsys.readouterr().out


def test_s26_reasoning_cases_and_exact_intentional_red_guidance():
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    learner = LEARNER_TEST.read_text(encoding="utf-8")
    normalized = " ".join(task.split())
    expected = "These tests are expected to fail until you complete the TODO functions."

    assert task.count(expected) == 1
    assert task.index(expected) < task.index(
        "python -m pytest -q lessons/sessions/s26/student/test_blueprint.py"
    )
    assert all(
        case in learner
        for case in (
            "test_valid_station_has_no_errors",
            "test_absent_required_id_fails_selection",
            "test_malformed_nested_shape_is_rejected",
            "test_duplicate_station_id_is_rejected",
            "test_selection_order_is_deterministic_and_stable",
            "test_acceptance_one_selected_station_becomes_one_package_object",
        )
    )
    assert all(
        phrase in normalized
        for phrase in (
            "at least three possible failure points",
            "which responsibility detects each failure",
            "one intermediate data shape",
        )
    )


def test_s26_learner_suite_is_red_in_pristine_state_and_outside_default_discovery():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(LEARNER_TEST)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "failed" in result.stdout
    assert LEARNER_TEST.parent != PROJECT_ROOT / "tests"


def test_s26_bounded_contract_implementation_can_make_learner_cases_green(monkeypatch):
    spec = importlib.util.spec_from_file_location("s26_learner_contract", LEARNER_TEST)
    assert spec is not None and spec.loader is not None
    learner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(learner)

    required = set(learner.starter.REQUIRED_STATION_FIELDS)

    def flatten_stations(expedition):
        if not isinstance(expedition, dict) or not isinstance(expedition.get("zones"), list):
            raise ValueError("zones must be a list")
        stations = []
        for zone in expedition["zones"]:
            if not isinstance(zone, dict) or not isinstance(zone.get("stations"), list):
                raise ValueError("each zone stations value must be a list")
            stations.extend(zone["stations"])
        return stations

    def validate_station(station):
        if not isinstance(station, dict):
            return ["station must be a dictionary"]
        return [f"missing field: {name}" for name in sorted(required - set(station))]

    def validate_expedition(expedition):
        try:
            stations = flatten_stations(expedition)
        except ValueError as error:
            return [str(error)]
        errors = [error for station in stations for error in validate_station(station)]
        seen = set()
        for station in stations:
            station_id = station.get("id")
            if station_id in seen:
                errors.append(f"duplicate station id: {station_id}")
            seen.add(station_id)
        return errors

    def select_stations(expedition, required_ids):
        errors = validate_expedition(expedition)
        if errors:
            raise ValueError("; ".join(errors))
        enabled = [station for station in flatten_stations(expedition) if station["enabled"]]
        selected = []
        for required_id in required_ids:
            match = next((station for station in enabled if station["id"] == required_id), None)
            if match is None:
                raise ValueError(f"absent required station id: {required_id}")
            selected.append(match)
        return sorted(selected, key=lambda station: station["route_order"])

    def build_package_preview(stations):
        objects = []
        for station in stations:
            objects.append(
                {
                    "id": station["id"],
                    "name": station["name"],
                    "x": station["coordinates"]["x"],
                    "y": station["coordinates"]["y"],
                    "color": station["color"],
                    "when_near": station["story"]["when_near"],
                    "when_interacted": station["story"]["when_interacted"],
                }
            )
        return {"objects": objects}

    monkeypatch.setattr(learner.starter, "flatten_stations", flatten_stations)
    monkeypatch.setattr(learner.starter, "validate_station", validate_station)
    monkeypatch.setattr(learner.starter, "validate_expedition", validate_expedition)
    monkeypatch.setattr(learner.starter, "select_stations", select_stations)
    monkeypatch.setattr(learner.starter, "build_package_preview", build_package_preview)

    learner.test_valid_station_has_no_errors()
    learner.test_absent_required_id_fails_selection()
    learner.test_malformed_nested_shape_is_rejected()
    learner.test_duplicate_station_id_is_rejected()
    learner.test_selection_order_is_deterministic_and_stable()
    learner.test_acceptance_one_selected_station_becomes_one_package_object()


def test_s26_student_spike_validates_plans_and_plays_existing_m03():
    loaded = load_explorer_package(STUDENT_PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (
            PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character",
            STUDENT_PACKAGE_ROOT,
        ),
        player_qualified_id="nova-character:nova",
    )
    manifest = yaml.safe_load((STUDENT_PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8"))

    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    objects = [item for item in manifest["contributions"] if item["type"] == "world_object"]
    assert len(objects) == 1

    scene = create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_03_ID)
    scene.enter()
    scene.update(DirectionalInput(), InteractionInput(interact_pressed=True), 0.0)
    assert scene.visited_qualified_ids == frozenset({"skyglass-observatory:echo-lens"})
    assert scene.mission_is_complete


def test_s26_student_package_differs_from_teacher_recovery_and_mapping_exists():
    student_manifest = yaml.safe_load(
        (STUDENT_PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8")
    )
    recovery_manifest = yaml.safe_load(
        (RECOVERY_PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8")
    )
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")

    assert load_explorer_package(RECOVERY_PACKAGE_ROOT).is_loaded
    assert student_manifest["package"]["id"] != recovery_manifest["package"]["id"]
    student_ids = {item["id"] for item in student_manifest["contributions"]}
    recovery_ids = {item["id"] for item in recovery_manifest["contributions"]}
    assert student_ids.isdisjoint(recovery_ids)
    assert all(
        phrase in task
        for phrase in (
            "Source data field",
            "Responsible Python function/module",
            "Resulting YAML/package field",
            "Visible Trail effect",
            "`story.when_near`",
            "`story.when_interacted`",
        )
    )


def test_s26_ai_git_cut_line_and_runtime_boundaries_are_explicit():
    runbook = (S26_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join((runbook + task).lower().split())

    assert "review exactly one student-written acceptance criterion for ambiguity" in normalized
    assert "identify ambiguity and ask a clarifying question" in normalized
    assert all(
        forbidden in normalized
        for forbidden in (
            "rewrite the entire criterion",
            "choose the premise",
            "create the responsibility map",
            "define function contracts",
            "write implementation",
            "generate the package",
            "provide test answers",
        )
    )
    assert "accept or reject" in normalized
    assert all(
        change in normalized
        for change in (
            "blueprint/project record",
            "initial tests",
            "playable spike",
        )
    )
    assert "status → diff → staged diff → descriptive commit" in normalized
    assert "one green acceptance test" in normalized
    assert "one validated student-owned playable object" in normalized
    assert all(
        deferred in normalized
        for deferred in (
            "complete module implementation",
            "full multi-object capstone",
            "extra mechanics",
            "polish",
        )
    )
    assert "do not add s27+ materials" in runbook.lower()
    assert "runtime/schema/api behavior" in runbook.lower()
    assert "deployment, authentication, or phase e" in runbook.lower()
