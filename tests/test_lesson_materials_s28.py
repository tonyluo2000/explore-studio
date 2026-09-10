from __future__ import annotations

import ast
import importlib.util
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from explore.curriculum.missions import MISSION_14_ID, MISSION_15_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from explore.packages.loader import load_explorer_package
from lessons.sessions.s28.student import integration
from lessons.sessions.s28.student.fixtures import (
    EXPECTED_ROUTE_IDS,
    EXPECTED_STYLE_ID,
    EXPECTED_STYLED_IDS,
    GOLDEN_FILE_LIST,
)

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
S28_ROOT = MATERIALS_ROOT / "s28"
STUDENT_ROOT = S28_ROOT / "student"
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
LEARNER_TEST = STUDENT_ROOT / "test_integration.py"


def _reference_load_plan(source_path=integration.SOURCE_PLAN_PATH):
    path = Path(source_path).resolve()
    root = integration.STUDENT_ROOT.resolve()
    if not path.is_relative_to(root):
        raise integration.InputPlanError(f"input path escapes student root: {path.name}")
    try:
        with path.open(encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
    except FileNotFoundError as error:
        raise integration.InputPlanError(f"missing input file: {path.name}") from error
    except yaml.YAMLError as error:
        raise integration.CorruptPlanError(f"corrupt YAML data: {path.name}") from error
    if not isinstance(loaded, dict) or not isinstance(loaded.get("zones"), list):
        raise integration.InputPlanError("input must be a mapping with a zones list")
    return loaded


def _reference_flatten(plan):
    return [station for zone in plan["zones"] for station in zone["stations"]]


def _reference_validate(plan):
    errors = []
    seen = set()
    duplicates = []
    for zone_index, zone in enumerate(plan["zones"]):
        stations = zone.get("stations")
        if not isinstance(stations, list):
            errors.append(f"zones[{zone_index}].stations must be a list")
            continue
        for station_index, station in enumerate(stations):
            location = f"zones[{zone_index}].stations[{station_index}]"
            order = station.get("route_order")
            if not isinstance(order, int) or isinstance(order, bool) or order <= 0:
                errors.append(f"{location}.route_order must be a positive integer")
            station_id = station.get("id")
            if station_id in seen and station_id not in duplicates:
                duplicates.append(station_id)
            seen.add(station_id)
    errors.extend(f"duplicate station id: {station_id}" for station_id in duplicates)
    return errors


def _reference_find_required(stations, required_ids):
    found = []
    for required_id in required_ids:
        match = next((station for station in stations if station["id"] == required_id), None)
        if match is None:
            raise ValueError(f"missing required station: {required_id}")
        found.append(match)
    return found


def _reference_select_enabled(stations):
    return [station for station in stations if station["enabled"]]


def _reference_order_route(stations):
    return sorted(stations, key=lambda station: station["route_order"])


def _reference_signal_total(stations):
    return sum(station["signal_power"] for station in stations)


def _reference_build_documents(plan, ordered_stations):
    package = plan["package"]
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
            "toggle_styles": [package["toggle_style"]],
            "contributions": contributions,
        },
        "objects": objects,
    }


def _reference_write_yaml(output_path, document):
    path = Path(output_path).resolve()
    root = integration.PACKAGE_ROOT.resolve()
    if not path.is_relative_to(root):
        raise integration.UnsafeIdentifierError("generated path escapes package root")
    rendered = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(rendered)
    return rendered


def _reference_build_package(plan):
    diagnostics = _reference_validate(plan)
    if diagnostics:
        raise integration.InvalidPlanError("; ".join(diagnostics))

    stations = _reference_flatten(plan)
    for station in stations:
        integration.safe_object_output_path(station["id"])
    guide = plan["sequence_guide"]
    integration.safe_object_output_path(guide["id"])

    found = _reference_find_required(stations, plan["required_station_ids"])
    selected = _reference_select_enabled(found)
    _reference_signal_total(selected)
    ordered = _reference_order_route(selected)
    documents = _reference_build_documents(plan, ordered)

    guide_path = f"character/{guide['id']}.yaml"
    documents["manifest"]["contributions"].append(
        {"id": guide["id"], "type": "character", "path": guide_path}
    )
    guide_document = {
        "name": guide["name"],
        "x": guide["x"],
        "y": guide["y"],
        "color": guide["color"],
        "respond_to_sequence": {
            "object_ids": [station["id"] for station in ordered],
            "when_incomplete": guide["when_incomplete"],
            "when_complete": guide["when_complete"],
        },
    }

    _reference_write_yaml(integration.PACKAGE_ROOT / "manifest.yaml", documents["manifest"])
    for item in documents["objects"]:
        station_id = Path(item["path"]).stem
        object_path = integration.safe_object_output_path(station_id)
        _reference_write_yaml(object_path, item["document"])
    _reference_write_yaml(integration.PACKAGE_ROOT / guide_path, guide_document)

    loaded = load_explorer_package(integration.PACKAGE_ROOT)
    if not loaded.is_loaded:
        details = "; ".join(
            f"{issue.code.value}:{issue.location}:{issue.message}" for issue in loaded.all_issues
        )
        raise integration.InvalidPlanError(details)
    return {
        "output_root": str(integration.PACKAGE_ROOT),
        "generated_files": GOLDEN_FILE_LIST,
        "validation_issues": (),
    }


def _load_learner_module():
    spec = importlib.util.spec_from_file_location("s28_learner_contract", LEARNER_TEST)
    assert spec is not None and spec.loader is not None
    learner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(learner)
    return learner


def _install_reference(monkeypatch, learner):
    monkeypatch.setattr(learner.integration, "load_plan", _reference_load_plan)
    monkeypatch.setattr(learner.integration, "write_yaml", _reference_write_yaml)
    monkeypatch.setattr(learner.integration, "build_package", _reference_build_package)


def test_s28_identity_classification_structure_and_exact_rhythm():
    runbook = (S28_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")

    assert runbook.startswith("# S28 — Capstone Integration")
    assert task.startswith("# S28 Task Card — Capstone Integration")
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
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(31, 32))


def test_s28_project_primary_structure_helpers_and_incomplete_scaffold(capsys):
    integration_source = (STUDENT_ROOT / "integration.py").read_text(encoding="utf-8")
    integration_tree = ast.parse(integration_source)
    functions = {
        node.name: node for node in integration_tree.body if isinstance(node, ast.FunctionDef)
    }
    starter_source = (STUDENT_ROOT / "starter.py").read_text(encoding="utf-8")
    starter_tree = ast.parse(starter_source)
    starter_functions = {
        node.name for node in starter_tree.body if isinstance(node, ast.FunctionDef)
    }

    assert all(name in functions for name in ("load_plan", "write_yaml", "build_package"))
    assert "main" in starter_functions
    for name in ("load_plan", "write_yaml", "build_package"):
        function_source = ast.get_source_segment(integration_source, functions[name])
        assert function_source is not None and "TODO" in function_source
    assert all(
        (STUDENT_ROOT / path).exists()
        for path in (
            "project-record.md",
            "source-plan.yaml",
            "fixtures.py",
            "fixtures/valid-plan.yaml",
            "test_integration.py",
            "explorer-package/manifest.yaml",
        )
    )
    namespace = runpy.run_path(str(STUDENT_ROOT / "starter.py"))
    namespace["main"]()
    assert "S28 integration scaffold ready" in capsys.readouterr().out


def test_s28_reuses_s27_modules_and_has_no_broad_exception_handler():
    source = (STUDENT_ROOT / "integration.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    defined = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]

    assert all(
        import_name in source
        for import_name in (
            "s27_builder",
            "s27_data_io",
            "s27_rules",
            "s27_validation",
        )
    )
    assert not defined.intersection(
        {
            "validate_plan",
            "flatten_stations",
            "find_required",
            "select_enabled",
            "order_route",
            "signal_total",
            "build_documents",
        }
    )
    assert handlers
    assert all(handler.type is not None for handler in handlers)
    assert "except Exception" not in source


def test_s28_safe_load_dump_input_output_and_path_boundaries_are_explicit():
    source = (STUDENT_ROOT / "integration.py").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    runbook = (S28_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    normalized = " ".join((task + runbook).lower().split())

    assert "yaml.safe_load" in source
    assert "yaml.safe_dump(document, sort_keys=False, allow_unicode=True)" in source
    assert all(
        phrase in normalized
        for phrase in (
            "source path inside the s28 student project area",
            "output root is the fixed s28",
            "not a caller-selected path",
            "accept arbitrary roots",
            "do not scan",
            "same input must produce the same file list, tree, and bytes",
            "validate every contribution id before constructing a path",
            "reject `../`, `/`, `\\\\`, absolute-path text",
        )
    )
    helper = source.split("def safe_object_output_path", 1)[1].split("\ndef ", 1)[0]
    assert helper.index("SAFE_IDENTIFIER.fullmatch") < helper.index('f"{contribution_id}.yaml"')


def test_s28_narrow_error_paths_and_no_repair_are_explicit():
    combined = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8") + (
        S28_ROOT / "teacher-runbook.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(combined.lower().split())

    assert all(
        phrase in combined for phrase in ("InputPlanError", "CorruptPlanError", "InvalidPlanError")
    )
    assert all(
        phrase in normalized
        for phrase in (
            "missing input file",
            "yaml parse failure",
            "preserving ordered diagnostics",
            "never use `except exception`",
            "silent fallback",
            "catch-and-ignore",
            "automatic repair",
            "never turn diagnostics into success",
        )
    )


def test_s28_exact_intentional_red_guidance_ratio_and_cases():
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    runbook = (S28_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    learner = LEARNER_TEST.read_text(encoding="utf-8")
    expected = "These tests are expected to fail until you complete the TODO functions."
    normalized = " ".join((task + runbook).lower().split())

    assert task.count(expected) == 1
    assert task.index(expected) < task.index(
        "python -m pytest -q lessons/sessions/s28/student/test_integration.py"
    )
    assert "6 failed / 2 passed" in normalized
    assert "missing-source" in normalized and "corrupt-yaml" in normalized
    assert "passes do not mean" in normalized
    assert all(
        case in learner
        for case in (
            "missing_source_file",
            "corrupt_yaml",
            "semantically_invalid_plan",
            "valid_source_generates_golden_file_list",
            "repeated_generation_is_byte_identical",
            "unsafe_identifier_rejected_before_path_construction",
            "generated_package_validates",
            "expected_m14_m15_structure",
        )
    )


def test_s28_learner_suite_is_red_and_outside_default_discovery():
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


def test_s28_bounded_reference_makes_all_learner_cases_green(tmp_path, monkeypatch):
    learner = _load_learner_module()
    _install_reference(monkeypatch, learner)

    for name in (
        "missing",
        "corrupt",
        "invalid",
        "success",
        "repeat",
        "unsafe",
        "validates",
        "structure",
    ):
        (tmp_path / name).mkdir()
    learner.test_missing_source_file_has_named_clear_error(tmp_path / "missing", monkeypatch)
    learner.test_corrupt_yaml_has_named_clear_error(tmp_path / "corrupt", monkeypatch)
    learner.test_semantically_invalid_plan_preserves_diagnostics(tmp_path / "invalid", monkeypatch)
    learner.test_valid_source_generates_golden_file_list(tmp_path / "success", monkeypatch)
    learner.test_repeated_generation_is_byte_identical(tmp_path / "repeat", monkeypatch)
    learner.test_unsafe_identifier_rejected_before_path_construction(
        tmp_path / "unsafe", monkeypatch
    )
    learner.test_generated_package_validates(tmp_path / "validates", monkeypatch)
    learner.test_generated_package_has_expected_m14_m15_structure(
        tmp_path / "structure", monkeypatch
    )


def test_s28_reference_generation_is_confined_and_byte_identical(tmp_path, monkeypatch):
    student_root = tmp_path / "student"
    student_root.mkdir()
    source_path = student_root / "valid-plan.yaml"
    shutil.copyfile(STUDENT_ROOT / "fixtures" / "valid-plan.yaml", source_path)
    monkeypatch.setattr(integration, "STUDENT_ROOT", student_root)
    monkeypatch.setattr(integration, "PACKAGE_ROOT", student_root / "explorer-package")
    plan = _reference_load_plan(source_path)

    first = _reference_build_package(plan)
    first_bytes = {
        path: (integration.PACKAGE_ROOT / path).read_bytes() for path in GOLDEN_FILE_LIST
    }
    second = _reference_build_package(plan)
    second_bytes = {
        path: (integration.PACKAGE_ROOT / path).read_bytes() for path in GOLDEN_FILE_LIST
    }

    assert first == second
    assert first_bytes == second_bytes
    assert tuple(first_bytes) == GOLDEN_FILE_LIST
    assert all(
        (integration.PACKAGE_ROOT / path)
        .resolve()
        .is_relative_to(integration.PACKAGE_ROOT.resolve())
        for path in GOLDEN_FILE_LIST
    )


def test_s28_reference_rejects_unsafe_id_before_constructing_output(tmp_path, monkeypatch):
    student_root = tmp_path / "student"
    student_root.mkdir()
    source_path = student_root / "unsafe-id-plan.yaml"
    shutil.copyfile(STUDENT_ROOT / "fixtures" / "unsafe-id-plan.yaml", source_path)
    monkeypatch.setattr(integration, "STUDENT_ROOT", student_root)
    monkeypatch.setattr(integration, "PACKAGE_ROOT", student_root / "explorer-package")
    plan = _reference_load_plan(source_path)

    try:
        _reference_build_package(plan)
    except integration.UnsafeIdentifierError as error:
        assert "../escape" in str(error)
    else:
        raise AssertionError("unsafe identifier was accepted")
    assert not integration.PACKAGE_ROOT.exists()


def test_s28_student_package_validates_plans_and_has_existing_m14_m15_structure():
    loaded = load_explorer_package(PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (
            PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character",
            PACKAGE_ROOT,
        ),
        player_qualified_id="nova-character:nova",
    )
    manifest = yaml.safe_load((PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    object_documents = {
        item["id"]: yaml.safe_load((PACKAGE_ROOT / item["path"]).read_text(encoding="utf-8"))
        for item in manifest["contributions"]
        if item["type"] == "world_object"
    }
    guide = yaml.safe_load(
        (PACKAGE_ROOT / "character" / "sky-guide.yaml").read_text(encoding="utf-8")
    )

    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    assert len(manifest["toggle_styles"]) == 1
    assert manifest["toggle_styles"][0]["id"] == EXPECTED_STYLE_ID
    assert (
        tuple(
            object_id
            for object_id, document in object_documents.items()
            if document.get("toggle_style_id") == EXPECTED_STYLE_ID
        )
        == EXPECTED_STYLED_IDS
    )
    assert tuple(guide["respond_to_sequence"]["object_ids"]) == EXPECTED_ROUTE_IDS
    assert create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_14_ID)
    assert create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_15_ID)


def test_s28_project_record_mapping_ai_git_and_cut_line_boundaries():
    record = (STUDENT_ROOT / "project-record.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    runbook = (S28_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    normalized = " ".join((task + runbook).lower().split())

    assert all(
        heading in record
        for heading in (
            "Generated-file and Trail predictions",
            "Four integration-path outcomes",
            "Safety and deterministic-export evidence",
            "Package and world evidence",
            "Integration/debugging decision",
            "Milestone self-review",
            "AI one-diagnostic receipt",
        )
    )
    assert all(
        mapping in task
        for mapping in (
            "Source plan field",
            "S27 helper",
            "Generated document/YAML",
            "Visible Trail behavior",
            "station `id`",
            "`coordinates`",
            "`color` / `toggle_style_id`",
            "story messages",
            "package `toggle_style`",
            "`required_station_ids`",
        )
    )
    assert "ai may interpret exactly one validator diagnostic" in normalized
    assert all(
        forbidden in normalized
        for forbidden in (
            "write i/o helpers",
            "generate yaml",
            "change package schema",
            "rewrite s27 logic",
            "choose exception handling",
            "provide final package contents",
        )
    )
    assert all(
        step in normalized
        for step in (
            "input loading + failure tests",
            "safe writer + deterministic-output tests",
            "package integration + validation evidence",
            "trail integration evidence",
            "no squash requirement",
        )
    )
    assert "only the expected m14" not in normalized
    assert "do not add s29+ materials" in runbook.lower()
    assert "engine/schema/student api/trail/mission/runtime" in runbook.lower()
    assert "deployment, authentication, or phase e" in runbook.lower()
    assert task.count("___") < record.count("___")
