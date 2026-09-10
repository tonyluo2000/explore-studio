from __future__ import annotations

import ast
import importlib.util
import runpy
import subprocess
import sys
from pathlib import Path

import yaml

from explore.curriculum.missions import MISSION_06_ID, MISSION_14_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
S27_ROOT = MATERIALS_ROOT / "s27"
STUDENT_ROOT = S27_ROOT / "student"
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
LEARNER_TEST = STUDENT_ROOT / "test_core.py"


def _flatten_stations(plan):
    return [station for zone in plan["zones"] for station in zone["stations"]]


def _validate_plan(plan):
    errors = []
    if not isinstance(plan, dict):
        return ["plan must be a dictionary"]
    if not isinstance(plan.get("name"), str) or not plan["name"].strip():
        errors.append("name must be a nonempty string")
    if not isinstance(plan.get("package"), dict):
        errors.append("package must be a dictionary")
    if not isinstance(plan.get("zones"), list):
        errors.append("zones must be a list")
        return errors

    seen = set()
    duplicates = []
    for zone_index, zone in enumerate(plan["zones"]):
        if not isinstance(zone, dict):
            errors.append(f"zones[{zone_index}] must be a dictionary")
            continue
        stations = zone.get("stations")
        if not isinstance(stations, list):
            errors.append(f"zones[{zone_index}].stations must be a list")
            continue
        for station_index, station in enumerate(stations):
            location = f"zones[{zone_index}].stations[{station_index}]"
            if not isinstance(station, dict):
                errors.append(f"{location} must be a dictionary")
                continue
            route_order = station.get("route_order")
            if (
                not isinstance(route_order, int)
                or isinstance(route_order, bool)
                or route_order <= 0
            ):
                errors.append(f"{location}.route_order must be a positive integer")
            station_id = station.get("id")
            if station_id in seen and station_id not in duplicates:
                duplicates.append(station_id)
            seen.add(station_id)
    errors.extend(f"duplicate station id: {station_id}" for station_id in duplicates)
    return errors


def _find_required(stations, required_ids):
    found = []
    for required_id in required_ids:
        match = next((station for station in stations if station["id"] == required_id), None)
        if match is None:
            raise ValueError(f"missing required station: {required_id}")
        found.append(match)
    return found


def _select_enabled(stations):
    return [station for station in stations if station["enabled"]]


def _order_route(stations):
    return sorted(stations, key=lambda station: station["route_order"])


def _signal_total(stations):
    return sum(station["signal_power"] for station in stations)


def _build_documents(plan, ordered_stations):
    package = plan["package"]
    style = package["toggle_style"]
    contributions = []
    objects = []
    for station in ordered_stations:
        path = f"objects/{station['id']}.yaml"
        contributions.append({"id": station["id"], "type": "world_object", "path": path})
        document = {
            "name": station["name"],
            "x": station["coordinates"]["x"],
            "y": station["coordinates"]["y"],
        }
        if "toggle_style_id" in station:
            document["when_near"] = station["story"]["when_near"]
            document["when_interacted"] = station["story"]["when_interacted"]
            document["toggle_style_id"] = station["toggle_style_id"]
        else:
            document["color"] = station["color"]
            document["when_near"] = station["story"]["when_near"]
            document["when_interacted"] = station["story"]["when_interacted"]
        objects.append({"path": path, "document": document})
    return {
        "manifest": {
            "schema_version": "0.2",
            "package": {
                "id": package["id"],
                "display_name": package["display_name"],
                "version": "0.1.0",
            },
            "compatibility": {"student_api": "0.1"},
            "toggle_styles": [style],
            "contributions": contributions,
        },
        "objects": objects,
    }


def test_s27_identity_classification_structure_and_exact_rhythm():
    runbook = (S27_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")

    assert runbook.startswith("# S27 — Capstone Core")
    assert task.startswith("# S27 Task Card — Capstone Core")
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
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(30, 31))


def test_s27_project_primary_modules_and_required_helpers_exist():
    expected_modules = {
        "data_io.py": ("flatten_stations",),
        "validation.py": ("validate_plan",),
        "rules.py": ("find_required", "select_enabled", "order_route", "signal_total"),
        "builder.py": ("build_documents",),
        "starter.py": ("main",),
    }

    for filename, helper_names in expected_modules.items():
        path = STUDENT_ROOT / filename
        assert path.is_file()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        assert set(helper_names) <= functions

    assert (STUDENT_ROOT / "project-record.md").is_file()
    assert (STUDENT_ROOT / "project_data.py").is_file()
    assert (STUDENT_ROOT / "fixtures.py").is_file()
    assert LEARNER_TEST.is_file()
    assert (PACKAGE_ROOT / "manifest.yaml").is_file()


def test_s27_required_helpers_are_meaningfully_incomplete_and_runner_is_thin(capsys):
    locations = {
        "validation.py": ("validate_plan",),
        "data_io.py": ("flatten_stations",),
        "rules.py": ("find_required", "select_enabled", "order_route", "signal_total"),
        "builder.py": ("build_documents",),
    }
    for filename, names in locations.items():
        source = (STUDENT_ROOT / filename).read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        for name in names:
            function_source = ast.get_source_segment(source, functions[name])
            assert function_source is not None and "TODO" in function_source
            assert len(functions[name].body) <= 2

    runpy.run_path(str(STUDENT_ROOT / "starter.py"), run_name="__main__")
    assert "S27 modular core scaffold ready" in capsys.readouterr().out


def test_s27_project_record_carries_forward_and_adds_core_evidence():
    record = (STUDENT_ROOT / "project-record.md").read_text(encoding="utf-8")

    assert record.startswith("# My Persistent Capstone Project Record — S27")
    assert all(
        heading in record
        for heading in (
            "Premise and acceptance criteria carried forward",
            "Responsibility map carried forward",
            "Accepted function contracts",
            "Whole-pipeline intermediate-value trace",
            "Implemented helpers and evidence",
            "Package-compatible output evidence",
            "Risks, refactoring, and deferred decisions",
            "Milestone self-review",
            "AI one-test receipt",
        )
    )
    assert all(
        field in record
        for field in (
            "Known risk 1",
            "Known risk 2",
            "One refactoring decision",
            "One decision deliberately deferred",
        )
    )


def test_s27_prediction_pipeline_validation_and_support_boundaries_are_explicit():
    runbook = (S27_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join((runbook + task).lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "input shape",
            "output shape",
            "one concrete example",
            "one failure/edge case",
            "one explicit intermediate-value trace",
            "ordered diagnostics",
            "flattened station records",
            "required-id search",
            "enabled filtering",
            "aggregation",
            "stable route ordering",
            "deterministic declarative document dictionaries",
        )
    )
    assert all(
        phrase in normalized
        for phrase in (
            "fail closed",
            "deterministic diagnostic ordering",
            "duplicate ids",
            "wrong",
            "invalid coordinate",
            "validation remains separate from file i/o",
            "pure rules remain file-free",
        )
    )
    assert "completed pure helper example only" in normalized
    assert "single_zone_reduced_plan" in normalized
    assert "support does not provide required helper bodies" in normalized


def test_s27_fixtures_are_fixed_complete_and_separate_from_editable_data():
    fixture_source = (STUDENT_ROOT / "fixtures.py").read_text(encoding="utf-8")
    project_source = (STUDENT_ROOT / "project_data.py").read_text(encoding="utf-8")
    fixtures = runpy.run_path(str(STUDENT_ROOT / "fixtures.py"))
    project = runpy.run_path(str(STUDENT_ROOT / "project_data.py"))

    assert "Students do not edit this file" in fixture_source
    assert "My editable S27 nested capstone plan" in project_source
    assert all(
        name in fixtures
        for name in (
            "ACCEPTED_S26_PLAN",
            "EMPTY_ZONE_PLAN",
            "MISSING_REQUIRED_STATION_PLAN",
            "WRONG_TYPE_RECORD_PLAN",
            "DUPLICATE_ID_PLAN",
            "STABLE_ORDER_TIE_PLAN",
            "EXPECTED_DOCUMENTS",
            "SINGLE_ZONE_REDUCED_PLAN",
        )
    )
    assert fixtures["ACCEPTED_S26_PLAN"] != project["PROJECT_PLAN"]


def test_s27_exact_intentional_red_guidance_and_learner_cases():
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    runbook = (S27_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    learner = LEARNER_TEST.read_text(encoding="utf-8")
    normalized_task = " ".join(task.lower().split())
    normalized_runbook = " ".join(runbook.lower().split())
    expected = "These tests are expected to fail until you complete the TODO functions."

    assert task.count(expected) == 1
    assert task.index(expected) < task.index(
        "python -m pytest -q lessons/sessions/s27/student/test_core.py"
    )
    assert "expected pristine result is **6 failed / 2 passed**" in normalized_task
    assert "test_accepted_s26_plan_has_no_diagnostics" in task
    assert "test_empty_zone_flattens_to_empty_list" in task
    assert "pass only because the current todo stubs return empty lists" in normalized_task
    assert "stub artifacts, not completed work" in normalized_task
    assert "both `validate_plan` and `flatten_stations` still need real implementations" in (
        normalized_task
    )
    assert "two green pristine tests are stub coincidences" in normalized_runbook
    assert "not proof that `validate_plan` or `flatten_stations` is complete" in (
        normalized_runbook
    )
    assert "do not let students skip either helper" in normalized_runbook
    assert "other failing cases as evidence" in normalized_runbook
    assert all(
        case in learner
        for case in (
            "accepted_s26_plan",
            "empty_zone",
            "missing_required_station",
            "wrong_type_record",
            "duplicate_id",
            "stable_tie",
            "signal_total",
            "exact_deterministic_output",
        )
    )


def test_s27_learner_suite_is_red_and_outside_default_discovery():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(LEARNER_TEST)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "6 failed, 2 passed" in result.stdout
    assert LEARNER_TEST.parent != PROJECT_ROOT / "tests"


def test_s27_bounded_reference_implementation_makes_learner_suite_green(monkeypatch):
    spec = importlib.util.spec_from_file_location("s27_learner_contract", LEARNER_TEST)
    assert spec is not None and spec.loader is not None
    learner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(learner)

    monkeypatch.setattr(learner.data_io, "flatten_stations", _flatten_stations)
    monkeypatch.setattr(learner.validation, "validate_plan", _validate_plan)
    monkeypatch.setattr(learner.rules, "find_required", _find_required)
    monkeypatch.setattr(learner.rules, "select_enabled", _select_enabled)
    monkeypatch.setattr(learner.rules, "order_route", _order_route)
    monkeypatch.setattr(learner.rules, "signal_total", _signal_total)
    monkeypatch.setattr(learner.builder, "build_documents", _build_documents)

    learner.test_accepted_s26_plan_has_no_diagnostics()
    learner.test_empty_zone_flattens_to_empty_list()
    learner.test_missing_required_station_fails_closed()
    learner.test_wrong_type_record_has_deterministic_diagnostic()
    learner.test_duplicate_id_fails_closed_after_record_checks()
    learner.test_find_filter_and_order_preserve_stable_tie()
    learner.test_signal_total_aggregates_selected_records()
    learner.test_build_documents_matches_exact_deterministic_output()


def test_s27_expected_documents_are_deterministic_exact_and_current_contract_only():
    fixtures = runpy.run_path(str(STUDENT_ROOT / "fixtures.py"))
    plan = fixtures["ACCEPTED_S26_PLAN"]
    stations = _flatten_stations(plan)
    selected = _select_enabled(_find_required(stations, plan["required_station_ids"]))
    documents = _build_documents(plan, _order_route(selected))

    assert documents == fixtures["EXPECTED_DOCUMENTS"]
    assert documents == _build_documents(plan, _order_route(selected))
    assert documents["manifest"]["schema_version"] == "0.2"
    assert len(documents["manifest"]["toggle_styles"]) == 1
    styled = [item for item in documents["objects"] if "toggle_style_id" in item["document"]]
    assert len(styled) == 2
    assert {item["document"]["toggle_style_id"] for item in styled} == {"storm-glow"}
    assert [item["path"] for item in documents["objects"]] == [
        "objects/north-lantern.yaml",
        "objects/harbor-beacon.yaml",
        "objects/summit-flare.yaml",
    ]


def test_s27_student_package_matches_project_output_validates_and_plans_m06_m14():
    project = runpy.run_path(str(STUDENT_ROOT / "project_data.py"))["PROJECT_PLAN"]
    stations = _flatten_stations(project)
    selected = _select_enabled(_find_required(stations, project["required_station_ids"]))
    documents = _build_documents(project, _order_route(selected))
    manifest = yaml.safe_load((PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    package_objects = [
        {
            "path": contribution["path"],
            "document": yaml.safe_load(
                (PACKAGE_ROOT / contribution["path"]).read_text(encoding="utf-8")
            ),
        }
        for contribution in manifest["contributions"]
    ]

    assert documents == {"manifest": manifest, "objects": package_objects}
    loaded = load_explorer_package(PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (
            PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character",
            PACKAGE_ROOT,
        ),
        player_qualified_id="nova-character:nova",
    )
    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    assert len(manifest["contributions"]) == 3
    assert len(manifest["toggle_styles"]) == 1
    styled = [item for item in package_objects if "toggle_style_id" in item["document"]]
    assert len(styled) == 2
    assert create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_06_ID)
    assert create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_14_ID)


def test_s27_no_yaml_writing_runtime_expansion_and_cut_line_are_explicit():
    runbook = (S27_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    combined = runbook + task
    normalized = " ".join(combined.lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "never writes yaml files",
            "does not serialize or write yaml",
            "s28 owns final package-file writing",
            "shared runtime consumes validated yaml only",
            "never runs student python",
            "existing m06 collection and m14 named-style behavior only",
            "no new package or runtime behavior",
        )
    )
    assert all(
        protected in normalized
        for protected in (
            "protect validation",
            "flattening",
            "selection/search rule",
            "stable ordering",
            "deterministic in-memory document output",
        )
    )
    assert "do not add s28+ materials" in runbook.lower()
    assert "engine/schema/student api/trail/mission/runtime" in runbook.lower()
    assert "deployment, authentication, or phase e" in runbook.lower()


def test_s27_ai_one_test_git_and_reduced_duplication_boundaries():
    runbook = (S27_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    record = (STUDENT_ROOT / "project-record.md").read_text(encoding="utf-8")
    normalized = " ".join((runbook + task).lower().split())

    assert "ai may propose exactly one failing test" in normalized
    assert "predicts why the test should fail" in normalized
    assert "decides whether to use it" in normalized
    assert "accept/reject reasoning" in normalized
    assert "implements all production code" in normalized
    assert all(
        forbidden in normalized
        for forbidden in (
            "write helper bodies",
            "choose module boundaries",
            "generate package documents",
            "solve validation",
            "provide final expected outputs",
        )
    )
    assert all(
        change in normalized
        for change in (
            "validation + tests",
            "flatten/search/filter + tests",
            "ordering/aggregation + tests",
            "document-builder + regression evidence",
            "no squash requirement",
        )
    )
    assert "only self-review and ai\nreceipt blanks" in task.lower()
    assert task.count("___") < record.count("___")
