from __future__ import annotations

import runpy
import shutil
from pathlib import Path

import pytest
import yaml

from explore.packages.classroom_trail import plan_local_classroom_trail
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
SESSIONS = {
    "s21": ("Package Gatekeeper", "build-an-object-collection"),
    "s22": ("Traceback Detective", "respond-to-object-state"),
    "s23": ("Builder's Workshop", "reuse-a-named-toggle-style"),
    "s24": ("Fast Ranger Index", "complete-actions-in-order"),
}
RUNBOOK_SECTIONS = (
    "Learning objective",
    "Prerequisite",
    "Before class",
    "45-minute runbook",
    "Teacher cut line",
    "Student task and prediction",
    "Deliberate debugging exercise",
    "Expected output and behavior",
    "Bounded AI assistance",
    "Git close",
    "Optional extension",
    "Teacher notes and answer key",
)
TASK_SECTIONS = (
    "Learning target",
    "Predict",
    "Core Python",
    "World payoff",
    "Support path",
    "Extension path",
    "Required evidence/checkpoints",
    "AI receipt",
    "Git close",
)


@pytest.mark.parametrize(("session", "title_mission"), SESSIONS.items())
def test_s21_s24_use_v2_structure_titles_and_existing_world_goals(
    session: str, title_mission: tuple[str, str]
) -> None:
    title, mission = title_mission
    session_root = MATERIALS_ROOT / session
    runbook = (session_root / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (session_root / "student" / "task-card.md").read_text(encoding="utf-8")
    starter = session_root / "student" / "starter.py"

    assert runbook.startswith(f"# {session.upper()} — {title}")
    assert task.startswith(f"# {session.upper()} Task Card — {title}")
    assert "**Role:** Python-primary software fluency" in task
    assert mission in task
    assert starter.is_file()
    assert "TODO" in starter.read_text(encoding="utf-8")
    assert all(section.lower() in runbook.lower() for section in RUNBOOK_SECTIONS)
    assert all(section.lower() in task.lower() for section in TASK_SECTIONS)
    assert "../../student-quick-start.md" in task
    assert all(anchor in runbook for anchor in ("0:00–0:04", "0:04–0:10", "0:10–0:28"))
    assert all(anchor in runbook for anchor in ("0:28–0:35", "0:35–0:42", "0:42–0:45"))


@pytest.mark.parametrize("session", SESSIONS)
def test_s21_s24_keep_ai_git_accessibility_and_runtime_boundaries(session: str) -> None:
    task = (MATERIALS_ROOT / session / "student" / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join(task.lower().split())

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
    assert "do not paste whole files or ask ai for a complete solution." in normalized
    assert "git diff --staged" in task
    assert all(item in normalized for item in ("`m`", "`??`", "no output", "identity"))
    assert "cancel/correct/retry" in normalized
    assert "understanding takes priority" in normalized
    assert "low bandwidth" in normalized
    assert (
        "python remains local" in normalized
        or "python and yaml file i/o remain local-only" in normalized
    )
    assert "validated declarative" in normalized


@pytest.mark.parametrize("session", SESSIONS)
def test_s21_s24_packages_validate_and_plan_with_existing_runtime(session: str) -> None:
    package_root = MATERIALS_ROOT / session / "student" / "explorer-package"
    loaded = load_explorer_package(package_root)
    plan = plan_local_classroom_trail(
        (PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character", package_root),
        player_qualified_id="nova-character:nova",
    )

    assert loaded.is_loaded, loaded.all_issues
    assert plan.is_planned, plan.issues


def test_s21_returns_ordered_diagnostics_and_invalid_package_fails_closed() -> None:
    student = MATERIALS_ROOT / "s21" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    validate_records = namespace["validate_records"]
    malformed = namespace["CASES"][1]

    assert validate_records(malformed[1]) == malformed[2]
    assert validate_records(["not-a-record"]) == ["record 1: expected a dictionary"]
    invalid = load_explorer_package(student / "invalid-package")
    assert not invalid.is_loaded
    assert any(issue.code.value == "FILE_MISSING" for issue in invalid.all_issues)

    task = (student / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join(task.split())
    assert all(
        phrase in task
        for phrase in ("missing fields", "wrong types", "invalid ranges", "duplicate ID")
    )
    assert "AI may supply at most one malformed example" in normalized
    assert "generic validation framework" in normalized


def test_s21_student_owns_a_bounded_repair_that_makes_the_package_validate(
    tmp_path: Path,
) -> None:
    """The invalid package must be repairable by authoring the file it promises."""
    student = MATERIALS_ROOT / "s21" / "student"
    declared = yaml.safe_load((student / "invalid-package" / "manifest.yaml").read_text("utf-8"))
    missing_paths = [
        entry["path"]
        for entry in declared["contributions"]
        if not (student / "invalid-package" / entry["path"]).exists()
    ]
    assert missing_paths, "S21 needs a real validation failure for the student to repair"

    repaired = tmp_path / "invalid-package"
    shutil.copytree(student / "invalid-package", repaired)
    for relative in missing_paths:
        target = repaired / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            'name: "Ridge Marker"\n'
            "x: 300\n"
            "y: 260\n"
            'color: "green"\n'
            'when_near: "The repaired record finally appears."\n'
            'when_interacted: "Gatekeeper repair accepted."\n',
            encoding="utf-8",
        )
    loaded = load_explorer_package(repaired)
    assert loaded.is_loaded, loaded.all_issues

    task = (student / "task-card.md").read_text(encoding="utf-8")
    runbook = (MATERIALS_ROOT / "s21" / "teacher-runbook.md").read_text(encoding="utf-8")
    normalized = " ".join(task.lower().split())
    assert "you repair the broken package" in normalized
    assert all(step in normalized for step in ("inspect first", "interpret it", "rerun"))
    assert "explain why it now passes" in normalized
    assert "student-owned action" in runbook.lower()
    assert "likely failure modes and recovery" in runbook.lower()


@pytest.mark.parametrize(
    ("session", "expected_output"),
    (
        ("s21", "valid []"),
        ("s22", "3 regression checks pass"),
        ("s23", "--- manifest.yaml ---"),
        ("s24", "small: (15, 6"),
    ),
)
def test_s21_s24_starters_are_runnable_and_incomplete(
    session: str, expected_output: str, capsys: pytest.CaptureFixture[str]
) -> None:
    starter = MATERIALS_ROOT / session / "student" / "starter.py"

    runpy.run_path(str(starter), run_name="__main__")

    assert expected_output in capsys.readouterr().out
    assert "TODO" in starter.read_text(encoding="utf-8")


def test_s22_ships_a_student_owned_bug_and_names_three_mistake_categories() -> None:
    """The student must repair a real bug in their own file, not only a fixture."""
    student = MATERIALS_ROOT / "s22" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    clues = namespace["CLUES"]

    assert namespace["clue_count"](clues) != len(clues), "S22 needs a live student-owned bug"
    assert namespace["clue_count"](clues) == len(clues) - 1

    task = (student / "task-card.md").read_text(encoding="utf-8")
    runbook = (MATERIALS_ROOT / "s22" / "teacher-runbook.md").read_text(encoding="utf-8")
    task_text = " ".join(task.lower().split())
    runbook_text = " ".join(runbook.lower().split())

    assert "observe → hypothesis → one change → rerun → compare evidence" in task_text
    assert "your own bug" in task_text
    assert "watch it **fail**" in task_text or "watch it fail" in task_text
    assert all(
        category in task_text
        for category in ("input mistake", "contract/validation mistake", "logic/behavior mistake")
    )
    assert all(
        category in runbook_text
        for category in (
            "syntax/input mistake",
            "contract/validation mistake",
            "logic/behavior mistake",
        )
    )
    assert "must resolve exactly once within this package" in runbook_text
    assert "student-owned action" in runbook_text
    assert "likely failure modes and recovery" in runbook_text


def test_s22_prepares_three_failures_and_requires_full_regression_workflow() -> None:
    student = MATERIALS_ROOT / "s22" / "student"
    debug = runpy.run_path(str(student / "debug.py"))
    task = (student / "task-card.md").read_text(encoding="utf-8")

    with pytest.raises(KeyError):
        debug["run_prepared_failure"]("key-error")
    with pytest.raises(IndexError):
        debug["run_prepared_failure"]("off-by-one")
    with pytest.raises(AssertionError):
        debug["run_prepared_failure"]("incorrect-return")

    normalized = " ".join(task.lower().split())
    assert all(item in task for item in ("`KeyError`", "`IndexError`", "incorrect-return"))
    assert "first relevant student-code frame" in normalized
    assert all(step in normalized for step in ("reproduce", "predict", "one change", "rerun"))
    assert "regression assertion" in normalized
    assert "one hint at a time only after you interpret the traceback" in normalized


def test_s23_requires_design_then_exact_behavior_preserving_modular_refactor() -> None:
    student = MATERIALS_ROOT / "s23" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    expected = (student / "expected-output.txt").read_text(encoding="utf-8")
    task = (student / "task-card.md").read_text(encoding="utf-8")

    assert namespace["pipeline_text"]() == expected
    assert all((student / name).is_file() for name in ("data_io.py", "rules.py", "build_output.py"))
    assert all(
        phrase in task
        for phrase in (
            "call/data flow",
            "data I/O",
            "validation/rules",
            "build/output",
            "exact-output regression",
            "M14 reuse analogy",
            "behavior-preserving refactor",
        )
    )
    assert "Do not add classes" in task
    assert "only after you identify a candidate" in task


def test_s23_composes_two_existing_mechanics_in_one_authored_package() -> None:
    """S23 rehearses S25: a shared toggle style and a keeper that reads one toggle."""
    student = MATERIALS_ROOT / "s23" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    documents = namespace["build_output"](namespace["load_data"](student / "workshop-plan.yaml"))
    manifest = documents["manifest.yaml"]

    styles = {style["id"] for style in manifest["toggle_styles"]}
    lamps = [
        documents[entry["path"]]
        for entry in manifest["contributions"]
        if entry["type"] == "world_object"
    ]
    keepers = [
        documents[entry["path"]]
        for entry in manifest["contributions"]
        if entry["type"] == "character"
    ]
    object_ids = {
        entry["id"] for entry in manifest["contributions"] if entry["type"] == "world_object"
    }

    assert len(styles) == 1
    assert len(lamps) >= 2
    assert {lamp["toggle_style_id"] for lamp in lamps} == styles
    assert len(keepers) == 1
    response = keepers[0]["respond_to_toggle"]
    assert response["object_id"] in object_ids, "the keeper must read a real object, not a fake one"
    assert response["when_off"] != response["when_on"]

    # The played package carries the same two mechanics.
    package_manifest = yaml.safe_load(
        (student / "explorer-package" / "manifest.yaml").read_text(encoding="utf-8")
    )
    types = [entry["type"] for entry in package_manifest["contributions"]]
    assert types.count("world_object") >= 2
    assert types.count("character") == 1
    assert len(package_manifest["toggle_styles"]) == 1


def test_s23_requires_a_student_authored_system_with_a_real_decision() -> None:
    student = MATERIALS_ROOT / "s23" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    placeholder = namespace["PLACEHOLDER"]
    my_system_text = (student / "my-system.yaml").read_text(encoding="utf-8")

    assert placeholder in my_system_text, "the authored decisions must still be the student's"
    with pytest.raises(ValueError, match=placeholder):
        namespace["compose_text"]()

    plan = yaml.safe_load(my_system_text)
    assert plan["keeper"]["watches"] == placeholder, "choosing the watched object is the decision"

    refactor_tests = (student / "test_refactor.py").read_text(encoding="utf-8")
    assert "test_my_system_composes_a_shared_style_and_a_responding_keeper" in refactor_tests
    assert "test_my_system_choices_are_my_own" in refactor_tests
    assert "test_pipeline_output_matches_exact_snapshot" in refactor_tests

    task = " ".join((student / "task-card.md").read_text(encoding="utf-8").lower().split())
    runbook = " ".join(
        (MATERIALS_ROOT / "s23" / "teacher-runbook.md").read_text(encoding="utf-8").lower().split()
    )
    assert "compose your own system" in task
    assert "which lamp the keeper watches" in task
    assert "student-owned action" in runbook
    assert "likely failure modes and recovery" in runbook


def test_s23_composition_rule_spans_both_mechanics() -> None:
    """A keeper that watches nothing in the plan is rejected before it is built."""
    namespace = runpy.run_path(str(MATERIALS_ROOT / "s23" / "student" / "starter.py"))
    plan = namespace["load_data"](MATERIALS_ROOT / "s23" / "student" / "workshop-plan.yaml")

    assert namespace["validate_data"](plan) == []

    orphaned = {**plan, "keeper": {**plan["keeper"], "watches": "no-such-lamp"}}
    assert "keeper must watch one of this plan's objects" in namespace["validate_data"](orphaned)

    identical = {
        **plan,
        "keeper": {**plan["keeper"], "when_on": plan["keeper"]["when_off"]},
    }
    assert "keeper off and on lines must differ" in namespace["validate_data"](identical)


def test_s24_improvement_preserves_behavior_and_makes_no_speed_claim() -> None:
    """S24 optimization means clarity, not unmeasured performance."""
    student = MATERIALS_ROOT / "s24" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    behavior_signature = namespace["behavior_signature"]
    starter_source = (student / "starter.py").read_text(encoding="utf-8")

    assert behavior_signature() == behavior_signature(), "the signature must be deterministic"
    briefing = namespace["route_briefing"]()
    assert briefing == [
        "Visit Signal Map first.",
        "Visit River Token second.",
        "Visit Summit Bell third.",
    ]
    # The fixture ships duplicated on purpose; that duplication is the student's work.
    assert starter_source.count('"Visit " + ') >= 3

    task = " ".join((student / "task-card.md").read_text(encoding="utf-8").lower().split())
    runbook = " ".join(
        (MATERIALS_ROOT / "s24" / "teacher-runbook.md").read_text(encoding="utf-8").lower().split()
    )
    assert "improve it without changing what it does" in task
    assert "it does **not** mean making it faster" in task
    assert "record the behavior first" in task
    assert "prove nothing changed" in task
    assert "student-owned action" in runbook
    assert "likely failure modes and recovery" in runbook
    assert "nothing here is timed, so nothing here can be called faster" in runbook


def test_s21_s24_bridge_to_s25_is_stated_in_order() -> None:
    """The mini-arc must name itself and sequence validate → debug → compose → optimize."""
    curriculum = (PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(curriculum.split())

    assert "Build Quality / Systems Practice" in normalized
    assert "Data Fluency → Validate → Debug → Compose → Optimize → Playable Prototype" in normalized
    assert "Milestone A" in normalized and "Milestone B" in normalized

    ownership = [
        normalized.index(phrase)
        for phrase in (
            "Fixes a bounded validity problem",
            "Diagnoses and repairs a deterministic bug",
            "Composes two supported mechanics into one authored system",
            "Improves that system while proving its behavior is unchanged",
        )
    ]
    assert ownership == sorted(ownership), "the ownership ladder must read S21 → S24 in order"

    for session in SESSIONS:
        runbook = (MATERIALS_ROOT / session / "teacher-runbook.md").read_text(encoding="utf-8")
        assert "Student-owned action" in runbook
        assert "Build Quality / Systems Practice" in runbook


def test_s25_plus_materials_are_untouched_by_this_arc() -> None:
    """S21–S24 refinement must not drift into S25+ implementation."""
    for number in range(25, 31):
        session = MATERIALS_ROOT / f"s{number}"
        assert (session / "teacher-runbook.md").is_file()
        assert (session / "student" / "task-card.md").is_file()


def test_s24_counts_inspections_rejects_duplicates_and_preserves_results() -> None:
    student = MATERIALS_ROOT / "s24" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    task = (student / "task-card.md").read_text(encoding="utf-8")

    assert namespace["compare"](6) == (15, 6, ["clue-4", "clue-5", "clue-6"])
    assert namespace["compare"](12) == (33, 12, ["clue-10", "clue-11", "clue-12"])
    duplicate = [{"id": "same"}, {"id": "same"}]
    with pytest.raises(ValueError, match="duplicate id"):
        namespace["build_id_index"](duplicate)

    normalized = " ".join(task.lower().split())
    assert "count inspected records, not seconds" in normalized
    assert "what happens to each count when the data doubles" in normalized
    assert "assert scanned == indexed" in task
    assert "no big-o notation is required" in normalized
    assert "do not create a runtime index/cache feature" in normalized


def test_no_s31_or_later_lesson_materials_exist() -> None:
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(31, 32))
