"""S25 — Milestone B / Playable Prototype lesson-material guards.

S25 is the first session a student owns end to end. These tests protect three
things the session cannot survive without: the starter must be *healthy but
unauthored*, the milestone must require **two** supported mechanics, and the
milestone checker must be able to go green for a real student completion.
"""

from __future__ import annotations

import ast
import itertools
import re
import runpy
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

from explore.curriculum.missions import MISSION_15_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from explore.packages.explorer_package_export import export_explorer_package
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
S25_ROOT = MATERIALS_ROOT / "s25"
STUDENT_ROOT = S25_ROOT / "student"
STUDENT_PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
RECOVERY_PACKAGE_ROOT = STUDENT_ROOT / "recovery-package"
NOVA_ROOT = PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character"
PLACEHOLDER = "CHOOSE-ME"

#: Every test the shipped milestone checker defines, in file order. A complete
#: student must turn all of them green, and nothing else may quietly appear or
#: vanish: :func:`_checker_test_names` holds this list to the real file.
MILESTONE_CHECKER_TESTS = (
    "test_plan_is_authored_before_the_build",
    "test_catalog_choices_are_authored",
    "test_package_text_is_authored",
    "test_pipeline_selects_aggregates_and_orders_the_route",
    "test_pipeline_refuses_invalid_and_absent_stations",
    "test_package_validates",
    "test_package_loads_and_plans_for_trail",
    "test_route_keeper_still_owns_an_exact_three_step_sequence",
    "test_two_supported_mechanics_are_present",
    "test_second_mechanic_is_wired_into_the_world",
    "test_build_is_deterministic",
    "test_pasted_evidence_matches_this_package",
    "test_reflection_is_complete",
    "test_reflection_explains_one_design_and_one_technical_decision",
)

#: The checker's red-on-download set: every one of these is student-owned work,
#: and none of them is an infrastructure failure in the shipped download.
MILESTONE_CHECKER_RED_ON_DOWNLOAD = (
    "test_plan_is_authored_before_the_build",
    "test_catalog_choices_are_authored",
    "test_package_text_is_authored",
    "test_pipeline_selects_aggregates_and_orders_the_route",
    "test_pipeline_refuses_invalid_and_absent_stations",
    "test_two_supported_mechanics_are_present",
    "test_second_mechanic_is_wired_into_the_world",
    "test_pasted_evidence_matches_this_package",
    "test_reflection_is_complete",
    "test_reflection_explains_one_design_and_one_technical_decision",
)

CLOCK_ANCHORS = (
    "0:00–0:05",
    "0:05–0:10",
    "0:10–0:25",
    "0:25–0:32",
    "0:32–0:38",
    "0:38–0:42",
    "0:42–0:45",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())


def _authored_strings(document, path: str = "") -> list[tuple[str, str]]:
    """Return (dotted path, value) for every string a student is meant to own."""
    if isinstance(document, str):
        return [(path, document)]
    if isinstance(document, dict):
        return [
            item
            for key, child in document.items()
            for item in _authored_strings(child, f"{path}.{key}" if path else str(key))
        ]
    if isinstance(document, list):
        return [
            item
            for index, child in enumerate(document)
            for item in _authored_strings(child, f"{path}[{index}]")
        ]
    return []


def _mechanic_families(package) -> set[str]:
    families = set()
    if any(character.respond_to_sequence is not None for character in package.characters):
        families.add("sequence")
    if any(item.counter is not None for item in package.world_objects):
        families.add("counter")
    if any(item.toggle is not None for item in package.world_objects):
        families.add("toggle")
    if any(
        character.greeting is not None or character.conversation is not None
        for character in package.characters
    ):
        families.add("dialogue")
    return families


def test_s25_milestone_b_identity_and_exact_rhythm():
    runbook = _read(S25_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")

    assert runbook.startswith("# S25 — Playable Prototype")
    assert task.startswith("# S25 Task Card — Playable Prototype")
    assert "**Role:** Project-primary production lesson" in runbook
    assert "**Role:** Project-primary production lesson" in task
    assert "**Milestone:** B — Playable Prototype" in runbook
    assert "Milestone:** B" in task
    assert all(anchor in runbook for anchor in CLOCK_ANCHORS)
    for name in (
        "starter.py",
        "fixtures.py",
        "test_pipeline.py",
        "test_milestone.py",
        "milestone.yaml",
        "project-record.md",
        "project_catalog.py",
    ):
        assert (STUDENT_ROOT / name).is_file(), name
    assert (STUDENT_PACKAGE_ROOT / "manifest.yaml").is_file()
    assert (RECOVERY_PACKAGE_ROOT / "manifest.yaml").is_file()
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(31, 32))


def test_s25_states_the_seven_milestone_acceptance_criteria():
    runbook = _normalized(_read(S25_ROOT / "teacher-runbook.md"))
    task = _normalized(_read(STUDENT_ROOT / "task-card.md"))

    for gate in ("plan", "build", "validate", "play", "compose", "debug", "explain"):
        assert f"**{gate}**" in task, gate
        assert f"**{gate}**" in runbook, gate
    assert "all seven, or it is not done" in task
    assert "all seven, or the milestone is incomplete" in runbook
    for document in (task, runbook):
        assert "two examples copied side by side do not pass" in document


def test_s25_one_milestone_contract_across_card_runbook_and_curriculum():
    """Criteria 2 and 7 must mean the same thing in every document that states them."""
    task = _read(STUDENT_ROOT / "task-card.md")
    runbook = _read(S25_ROOT / "teacher-runbook.md")
    curriculum = " ".join(_read(PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md").split())
    checker = _read(STUDENT_ROOT / "test_milestone.py")

    # Criterion 2 includes the pipeline, and the checker really enforces it.
    assert "`starter.py` pipeline runs" in task
    assert "`starter.py` pipeline runs" in runbook
    assert (
        "one meaningful algorithmic pipeline, completed and checked by the milestone checker"
        in curriculum
    )
    assert "criterion 2 includes the pipeline" in _normalized(task + runbook)
    assert "pipeline.build_preview" in checker and "pipeline.select_route" in checker

    # Criterion 7 names two fields that exist, and the checker requires both.
    for field in ("design_decision", "technical_decision"):
        assert field in task, field
        assert field in runbook, field
        assert field in curriculum, field
        assert f'"{field}"' in checker, field
    assert "test_reflection_explains_one_design_and_one_technical_decision" in checker


def test_s25_starter_package_is_valid_but_entirely_unauthored():
    """The download must be healthy; only the student's decisions are missing."""
    loaded = load_explorer_package(STUDENT_PACKAGE_ROOT)
    assert loaded.is_loaded, loaded.all_issues

    planned = plan_local_classroom_trail(
        (NOVA_ROOT, STUDENT_PACKAGE_ROOT), player_qualified_id="nova-character:nova"
    )
    assert planned.is_planned, planned.issues
    assert planned.plan is not None

    scene = create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_15_ID)
    for object_id in ("first-stop", "second-stop", "third-stop"):
        scene._update_sequence_progress(f"my-playable-prototype:{object_id}")
    assert scene.mission_is_complete

    unauthored = []
    for path in sorted(STUDENT_PACKAGE_ROOT.rglob("*.yaml")):
        document = yaml.safe_load(_read(path))
        relative = path.relative_to(STUDENT_PACKAGE_ROOT).as_posix()
        unauthored += [
            f"{relative}:{field}"
            for field, value in _authored_strings(document)
            if PLACEHOLDER in value
        ]
    assert {
        "manifest.yaml:package.display_name",
        "character/route-keeper.yaml:name",
        "character/route-keeper.yaml:respond_to_sequence.when_complete",
        "objects/first-stop.yaml:when_near",
    } <= set(unauthored), unauthored

    assert _mechanic_families(loaded.package) == {
        "sequence"
    }, "the starter must ship one mechanic so the student genuinely adds the second"


def test_s25_catalog_is_unauthored_and_plans_the_second_mechanic():
    catalog = runpy.run_path(str(STUDENT_ROOT / "project_catalog.py"))
    source = _read(STUDENT_ROOT / "project_catalog.py")
    fixtures = runpy.run_path(str(STUDENT_ROOT / "fixtures.py"))

    stations = catalog["PROJECT_CATALOG"]["regions"][0]["stations"]
    assert len(stations) == 3
    assert tuple(station["id"] for station in stations) == catalog["PROJECT_ROUTE_IDS"]
    assert catalog["PROJECT_CATALOG"] != fixtures["NORMAL_CATALOG"]
    assert all(
        set(station) == {"id", "name", "enabled", "route_order", "signal_power", "world"}
        for station in stations
    )
    assert all(station["name"] == PLACEHOLDER for station in stations)
    assert all(
        station["world"][field] == PLACEHOLDER
        for station in stations
        for field in ("when_near", "when_interacted")
    )
    assert catalog["SECOND_MECHANIC"] == {
        "kind": PLACEHOLDER,
        "object_id": PLACEHOLDER,
        "relationship": PLACEHOLDER,
    }
    assert "Safe bounds" in source
    assert "Students should not edit these test fixtures" in _read(STUDENT_ROOT / "fixtures.py")


def test_s25_milestone_artifact_holds_the_plan_the_reflection_and_the_evidence():
    document = yaml.safe_load(_read(STUDENT_ROOT / "milestone.yaml"))

    assert set(document) == {"plan", "reflection", "evidence"}
    assert set(document["plan"]) == {
        "premise",
        "mechanics",
        "how_they_connect",
        "player_action",
        "expected_result",
    }
    assert document["plan"]["mechanics"] == ["sequence", PLACEHOLDER]
    assert set(document["reflection"]) == {
        "what_i_built",
        "two_mechanics_i_combined",
        "problem_and_how_i_fixed_it",
        "fifteen_more_minutes",
        "design_decision",
        "technical_decision",
    }
    assert set(document["evidence"]) == {"package_validation", "build_digest", "trail_result"}
    assert all(value == PLACEHOLDER for _, value in _authored_strings(document["reflection"]))
    assert all(value == PLACEHOLDER for _, value in _authored_strings(document["evidence"]))

    task = _read(STUDENT_ROOT / "task-card.md")
    for question in (
        "What did you choose to build?",
        "Which two mechanics did you combine?",
        "What problem did you hit and how did you fix it?",
        "What would you improve with 15 more minutes?",
        "One design decision you made, and why?",
        "One technical decision you made, and why?",
    ):
        assert question in task, question


class CheckerRun(NamedTuple):
    """One milestone-checker subprocess: what passed, what did not, and the proof."""

    passed: frozenset[str]
    failed: frozenset[str]
    returncode: int
    output: str


def _checker_test_names() -> tuple[str, ...]:
    """Every test the shipped checker actually defines, in file order."""
    tree = ast.parse(_read(STUDENT_ROOT / "test_milestone.py"))
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )


def _run_milestone_checker(checker_path: Path) -> CheckerRun:
    """Run one milestone checker and report every per-test outcome it printed."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--tb=short",
            "-v",
            str(checker_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # `-v` prints one `path::name OUTCOME` line per test, so a run that dies in
    # collection reports no outcomes at all rather than looking quietly clean.
    outcomes = dict(
        re.findall(
            r"::(\w+) (PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)",
            completed.stdout,
        )
    )
    passed = frozenset(name for name, outcome in outcomes.items() if outcome == "PASSED")
    not_passed = frozenset(name for name, outcome in outcomes.items() if outcome != "PASSED")
    return CheckerRun(passed, not_passed, completed.returncode, completed.stdout)


def test_s25_milestone_checker_is_red_only_for_unmade_decisions():
    """The shipped state must fail for ownership reasons, never infrastructure ones."""
    assert _checker_test_names() == MILESTONE_CHECKER_TESTS, _checker_test_names()

    run = _run_milestone_checker(STUDENT_ROOT / "test_milestone.py")

    assert run.returncode != 0, "the shipped download must start red"
    assert run.passed | run.failed == set(MILESTONE_CHECKER_TESTS), run.output
    assert run.failed == set(MILESTONE_CHECKER_RED_ON_DOWNLOAD), run.output
    for infrastructure in (
        "test_package_validates",
        "test_package_loads_and_plans_for_trail",
        "test_route_keeper_still_owns_an_exact_three_step_sequence",
        "test_build_is_deterministic",
    ):
        assert infrastructure in run.passed, f"{infrastructure} must be green on the download"


def _student_workspace(tmp_path: Path) -> Path:
    """Reproduce the student's course-folder layout so the checker resolves Nova."""
    root = tmp_path / "lessons" / "sessions" / "s25" / "student"
    root.parent.mkdir(parents=True)
    shutil.copytree(STUDENT_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(NOVA_ROOT, tmp_path / "examples" / "explorer-packages" / "nova-character")
    return root


#: One correct completion of the four ``starter.py`` TODO bodies. The simulated
#: student has to finish the pipeline like any other student: criterion 2
#: includes it, so the checker cannot go green without it.
COMPLETED_PIPELINE = '''def validate_station(station):
    """Return errors for the prepared station shape; an empty list means valid."""
    errors = []
    if not isinstance(station, dict):
        return ["station must be a dictionary"]
    for field in REQUIRED_STATION_FIELDS:
        if field not in station:
            errors.append(f"{field} is missing")
    world = station.get("world")
    if not isinstance(world, dict):
        return errors + ["world must be a dictionary"]
    for field in REQUIRED_WORLD_FIELDS:
        if field not in world:
            errors.append(f"world.{field} is missing")
    if errors:
        return errors
    if not isinstance(station["enabled"], bool):
        errors.append("enabled must be true or false")
    if not isinstance(station["route_order"], int) or station["route_order"] < 1:
        errors.append("route_order must be a positive integer")
    if not isinstance(station["signal_power"], int) or station["signal_power"] < 0:
        errors.append("signal_power must be a nonnegative integer")
    for axis in ("x", "y"):
        value = world[axis]
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"{axis} must be an integer")
        elif not 40 <= value <= 760:
            errors.append(f"{axis} must be from 40 through 760")
    return errors


def select_route(catalog, required_ids):
    """Return exactly three enabled required stations in requested-ID order."""
    selected = []
    enabled = [station for station in catalog_stations(catalog) if station["enabled"]]
    for required in required_ids:
        found = None
        for station in enabled:
            if station["id"] == required:
                found = station
                break
        if found is None:
            raise ValueError(f"required station {required} is not available")
        selected.append(found)
    if len(selected) != 3:
        raise ValueError("exactly three required stations must be selected")
    return selected


def signal_total(stations):
    """Return the sum of signal_power for the selected stations."""
    total = 0
    for station in stations:
        total += station["signal_power"]
    return total


def ordered_route(stations):
    """Return a stable sorted copy using route_order only."""
    return sorted(stations, key=lambda station: station["route_order"])


'''


def _complete_pipeline(starter_path: Path) -> None:
    """Replace the four TODO bodies with one working implementation."""
    head, marker, rest = _read(starter_path).partition("def validate_station")
    assert marker, "starter.py must still define validate_station"
    _, marker, tail = rest.partition("def transform_preview")
    assert marker, "starter.py must still define transform_preview"
    starter_path.write_text(head + COMPLETED_PIPELINE + marker + tail, encoding="utf-8")


def _author_student_copy(root: Path) -> None:
    """Do what one student does: choose a premise, a second mechanic, and words."""
    package = root / "explorer-package"

    _complete_pipeline(root / "starter.py")

    # Catalog: the second-mechanic plan first, then the story text.
    catalog_path = root / "project_catalog.py"
    text = _read(catalog_path)
    text = text.replace(f'"kind": "{PLACEHOLDER}"', '"kind": "counter"')
    text = text.replace(f'"object_id": "{PLACEHOLDER}"', '"object_id": "third-stop"')
    text = text.replace(
        f'"relationship": "{PLACEHOLDER}"',
        '"relationship": "The last stop is also the beacon, so the final step charges it."',
    )
    numbers = itertools.count(1)
    text = re.sub(f'"{PLACEHOLDER}"', lambda _: f'"Tidepool Watch line {next(numbers)}"', text)
    catalog_path.write_text(text, encoding="utf-8")

    # Package: author every string, then add the counter and the keeper reading it.
    for path in sorted(package.rglob("*.yaml")):
        document = yaml.safe_load(_read(path))
        authored = _authored_strings(document)
        for field, value in authored:
            if PLACEHOLDER not in value:
                continue
            target = document
            *parents, leaf = field.split(".")
            for key in parents:
                target = target[key]
            target[leaf] = f"Tidepool Watch {path.stem} {leaf}"
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    third = package / "objects" / "third-stop.yaml"
    document = yaml.safe_load(_read(third))
    document["counter"] = {
        "goal": 2,
        "when_goal_reached": "The beacon burns bright enough for the harbor.",
    }
    third.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    (package / "character" / "signal-keeper.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "Beacon Watcher",
                "x": 140,
                "y": 460,
                "color": "pink",
                "respond_to_counter": {
                    "object_id": "third-stop",
                    "when_below_goal": "The beacon is lit but still faint.",
                    "when_at_or_above_goal": "The harbor can see us now.",
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest_path = package / "manifest.yaml"
    manifest = yaml.safe_load(_read(manifest_path))
    manifest["contributions"].append(
        {"id": "signal-keeper", "type": "character", "path": "character/signal-keeper.yaml"}
    )
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    # Evidence comes from the package as it now stands.
    loaded = load_explorer_package(package)
    assert loaded.is_loaded, loaded.all_issues
    metadata = loaded.package.metadata
    archive = root.resolve() / f"{metadata.id}-{metadata.version}.explorer-package.zip"
    exported = export_explorer_package(package, archive)
    assert exported.is_exported, exported.issues
    archive.unlink()

    milestone_path = root / "milestone.yaml"
    milestone = yaml.safe_load(_read(milestone_path))
    milestone["plan"] |= {
        "premise": "A tidepool watch that has to be walked in order at dusk.",
        "mechanics": ["sequence", "counter"],
        "how_they_connect": "The last stop of the route is the beacon the watcher reads.",
        "player_action": "Walk the three stops in order, then charge the beacon.",
        "expected_result": "The route keeper opens the watch and the watcher confirms the beacon.",
    }
    milestone["reflection"] |= {
        "what_i_built": "A dusk tidepool watch with three stops and a beacon.",
        "two_mechanics_i_combined": "The M15 ordered route and a counter on the last stop.",
        "problem_and_how_i_fixed_it": (
            "My watcher pointed at the first stop, which has no counter, so validation "
            "refused it; I pointed it at the third stop instead and it passed."
        ),
        "fifteen_more_minutes": "Better dusk wording at the second stop.",
        "design_decision": (
            "I put the counter on the last stop so one walk of the route also "
            "charges the beacon, and the watcher has something to notice."
        ),
        "technical_decision": (
            "validate_station returns every error it finds instead of the first, "
            "so one run names all the bad fields."
        ),
    }
    milestone["evidence"] |= {
        "package_validation": f"valid: {metadata.id} {metadata.version}",
        "build_digest": exported.digest.hex_digest,
        "trail_result": "Correct order opened the watch; a wrong stop reset it to zero.",
    }
    milestone_path.write_text(yaml.safe_dump(milestone, sort_keys=False), encoding="utf-8")


def test_s25_milestone_checker_goes_green_for_a_complete_student(tmp_path):
    """One simulated student completion must satisfy every acceptance criterion."""
    root = _student_workspace(tmp_path)
    _author_student_copy(root)

    run = _run_milestone_checker(root / "test_milestone.py")
    # Green means the whole checker ran and every named test passed. Asserting
    # only "nothing FAILED" would also accept a run that died in collection.
    assert run.returncode == 0, run.output
    assert not run.failed, run.output
    assert run.passed == set(MILESTONE_CHECKER_TESTS), run.output
    assert len(run.passed) == len(MILESTONE_CHECKER_TESTS), run.output

    planned = plan_local_classroom_trail(
        (NOVA_ROOT, root / "explorer-package"), player_qualified_id="nova-character:nova"
    )
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_15_ID)
    for object_id in ("first-stop", "second-stop", "third-stop"):
        scene._update_sequence_progress(f"my-playable-prototype:{object_id}")
    assert scene.mission_is_complete
    assert scene._counter_counts == {"my-playable-prototype:third-stop": 0}


def test_s25_milestone_checker_names_an_invalid_package_separately(tmp_path):
    """An invalid package must read as invalid, not as an unmade decision."""
    root = _student_workspace(tmp_path)
    _author_student_copy(root)

    keeper = root / "explorer-package" / "character" / "signal-keeper.yaml"
    document = yaml.safe_load(_read(keeper))
    document["respond_to_counter"]["object_id"] = "first-stop"
    keeper.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    run = _run_milestone_checker(root / "test_milestone.py")

    assert run.returncode != 0, run.output
    assert "test_package_validates" in run.failed, run.output
    assert "must reference a world object with counter metadata" in run.output
    assert "test_reflection_is_complete" in run.passed, run.output
    assert "test_plan_is_authored_before_the_build" in run.passed, run.output


def test_s25_pipeline_scaffold_stays_incomplete_and_five_cases_stay_explicit(capsys):
    source = _read(STUDENT_ROOT / "starter.py")
    task = _read(STUDENT_ROOT / "task-card.md")
    tests = _read(STUDENT_ROOT / "test_pipeline.py")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

    for name in ("validate_station", "select_route", "signal_total", "ordered_route"):
        assert name in functions
        function_source = ast.get_source_segment(source, functions[name])
        assert function_source is not None and "TODO" in function_source
    runpy.run_path(str(STUDENT_ROOT / "starter.py"), run_name="__main__")
    assert "S25 scaffold ready" in capsys.readouterr().out

    assert (
        "validate → filter enabled → search required IDs → count selected\n"
        "→ aggregate signal power → stable sort → transform preview"
    ) in task
    assert "sorted(..., key=...)" in source
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
    expected = "These pipeline tests are expected to fail until you complete the TODO\nfunctions."
    assert task.count(expected) == 1
    assert task.index(expected) < task.index(
        "explore-package validate lessons/sessions/s25/student/explorer-package"
    )
    assert "python -m pytest -q lessons/sessions/s25/student/test_milestone.py" in task


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
    assert [station["route_order"] for station in regression["regions"][0]["stations"]] == [1, 1, 2]


def test_s25_recovery_package_demonstrates_two_mechanics_and_exact_m15():
    loaded = load_explorer_package(RECOVERY_PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (NOVA_ROOT, RECOVERY_PACKAGE_ROOT), player_qualified_id="nova-character:nova"
    )
    manifest = yaml.safe_load(_read(RECOVERY_PACKAGE_ROOT / "manifest.yaml"))
    keeper = yaml.safe_load(_read(RECOVERY_PACKAGE_ROOT / "character" / "rescue-keeper.yaml"))

    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    assert _mechanic_families(loaded.package) == {"sequence", "counter"}
    world_contributions = [
        item for item in manifest["contributions"] if item["type"] == "world_object"
    ]
    assert len(world_contributions) == 3
    assert keeper["respond_to_sequence"]["object_ids"] == [
        "harbor-drum",
        "north-lantern",
        "summit-flare",
    ]
    watcher = yaml.safe_load(_read(RECOVERY_PACKAGE_ROOT / "character" / "flare-watcher.yaml"))
    assert watcher["respond_to_counter"]["object_id"] == "summit-flare"

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

    boundary = _normalized(
        _read(S25_ROOT / "teacher-runbook.md") + _read(STUDENT_ROOT / "task-card.md")
    )
    assert "teacher-only" in boundary
    assert "partial recovery" in boundary
    assert "does not complete" in boundary
    assert "later finish" in boundary
    assert "every prediction" in boundary
    assert "at least one completed function" in boundary


def test_s25_runbook_covers_pacing_failure_modes_degraded_mode_and_cut_line():
    runbook = _read(S25_ROOT / "teacher-runbook.md")
    normalized = _normalized(runbook)

    assert "## Likely failure modes and recovery" in runbook
    assert "## Degraded mode if Trail will not launch" in runbook
    assert "## Teacher cut line" in runbook
    assert "## Milestone evidence" in runbook
    assert "## Student-owned decisions" in runbook
    for diagnostic in (
        "color cannot be combined with toggle",
        "must reference a world object with counter metadata",
        "goal must be from 2 through 5",
    ):
        assert diagnostic in runbook, diagnostic
    assert "never cut to one mechanic" in normalized
    assert "text-only" in normalized
    assert "do not manufacture one for every student" in normalized
    assert "one bounded fallback" in normalized


def test_s25_engine_honesty_documents_only_supported_mechanics():
    runbook = _read(S25_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    normalized = _normalized(runbook + task)

    assert "counters increment only" in normalized
    assert "whole numbers from 2 through 5" in normalized
    assert "one character carries at most one response mechanic" in normalized
    for absent in (
        "no persistence across sessions",
        "no inventory",
        "no collision or physical\nlocking",
        "no arbitrary variable store",
        "no cross-package semantic reference",
    ):
        assert absent in runbook, absent
    assert "the fix is the wording of the premise, not the engine" in normalized
    # Nothing may promise state the runtime does not keep.
    for forbidden in ("save your progress", "inventory", "health bar", "score"):
        assert forbidden not in _normalized(task), forbidden


def test_s25_names_the_s21_s24_arc_and_holds_the_s26_boundary():
    runbook = _read(S25_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    curriculum = _read(PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md")
    normalized = _normalized(runbook + task)

    assert "Validate → Debug → Compose → Optimize → **Playable Prototype**" in task
    assert "Build Quality / Systems Practice" in runbook
    assert "(S21" in task and "S22" in task and "S23" in task and "S24" in task
    for document in (runbook, task):
        assert "I can independently build and explain a small\nworking system" in document or (
            "i can independently build and explain a small working system" in _normalized(document)
        )
    assert "i can design my own larger capstone" in normalized
    assert "do not let a student start designing the" in normalized

    curriculum_normalized = " ".join(curriculum.split())
    assert (
        "Data Fluency → Validate → Debug → Compose → Optimize → Playable Prototype "
        "→ Capstone Blueprint." in curriculum_normalized
    )
    assert "at least two supported Trail mechanics coexisting meaningfully" in curriculum_normalized
    assert "The capstone build plan belongs to S26, not here." in curriculum_normalized
    assert "S20 is Milestone A" in curriculum
    assert "S25, **Milestone B**" in curriculum


def test_s25_ai_git_self_review_support_and_runtime_boundaries_are_explicit():
    task = _read(STUDENT_ROOT / "task-card.md")
    normalized = _normalized(task)

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
    assert "Planning and prototype implementation belong in separate commits" in task
    assert "git status --short" in task and "git diff --staged" in task
    assert all(item in normalized for item in ("`m`", "`??`", "no output", "identity"))
    assert "python stays local" in normalized
    assert "local python helps you reason, transform, and validate" in normalized
    assert "validated package yaml drives the visible world" in normalized
    assert "shared runtime never executes student python" in normalized
    assert "do not add fields to the runtime schema" in normalized
    assert "do not add a fourth sequence member" in normalized

    record = _read(STUDENT_ROOT / "project-record.md")
    assert "AI receipt" in record
    assert "Predictions before running" in record
