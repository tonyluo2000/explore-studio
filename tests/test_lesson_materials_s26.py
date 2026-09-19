"""S26 — Capstone Blueprint lesson-material guards.

S26 is the course's only planning-primary session, and the two ways it can fail
are opposites. It can drift back into implementation, which is S27's work and
would leave students with no design; or its blueprint can invite a capstone the
runtime cannot run and four sessions cannot finish.

These tests hold both lines. The session must ship exactly one student-owned
blueprint and no starter modules, fixtures, or package; and the shipped gate
must refuse an over-scoped plan, an unsupported mechanic, an unconnected pair,
an unbounded S27 target, and a missing fallback — while going green for a real
student design.
"""

from __future__ import annotations

import ast
import os
import re
import runpy
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
S26_ROOT = MATERIALS_ROOT / "s26"
STUDENT_ROOT = S26_ROOT / "student"
EXAMPLES_ROOT = STUDENT_ROOT / "examples"
BLUEPRINT_PATH = STUDENT_ROOT / "capstone-blueprint.yaml"
RIGHT_SIZED = EXAMPLES_ROOT / "right-sized-blueprint.yaml"
TOO_BIG = EXAMPLES_ROOT / "too-big-blueprint.yaml"
CHECKER = STUDENT_ROOT / "test_blueprint.py"
PLACEHOLDER = "CHOOSE-ME"

#: Every test the shipped blueprint checker defines, in file order. The nine
#: completion-gate items map onto these; nothing may quietly appear or vanish.
BLUEPRINT_CHECKER_TESTS = (
    "test_no_unmade_decisions",
    "test_premise_and_player_goal_are_specific",
    "test_mechanics_are_two_to_four_supported_kinds",
    "test_every_mechanic_has_a_role_in_the_player_experience",
    "test_two_mechanics_are_really_connected",
    "test_world_has_two_to_four_key_elements",
    "test_player_flow_is_three_to_six_concrete_steps",
    "test_s27_first_slice_is_bounded",
    "test_risk_and_fallback_are_named",
    "test_nothing_needs_a_feature_the_runtime_does_not_have",
    "test_reflection_explains_the_choice",
)

#: The only checker test that may be green on the download: the shipped
#: placeholders ask for nothing the runtime lacks. Every other test is a
#: decision the student has not made yet.
BLUEPRINT_GREEN_ON_DOWNLOAD = ("test_nothing_needs_a_feature_the_runtime_does_not_have",)

#: Mechanic names the student may write. Sourced from the shipped menu so this
#: list and the menu cannot drift apart.
MENU = runpy.run_path(str(STUDENT_ROOT / "mechanic_menu.py"))
SUPPORTED_KINDS = frozenset(MENU["SUPPORTED_MECHANICS"])


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())


def _load(path: Path) -> dict:
    return yaml.safe_load(_read(path))


class CheckerRun(NamedTuple):
    """One blueprint-checker subprocess: what passed, what did not, and the proof."""

    passed: frozenset[str]
    failed: frozenset[str]
    returncode: int
    output: str


def _run_checker(checker_path: Path, blueprint: Path | None = None) -> CheckerRun:
    """Run one blueprint checker and report every per-test outcome it printed."""
    environment = None
    if blueprint is not None:
        environment = os.environ | {"BLUEPRINT": str(blueprint)}
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
        env=environment,
    )
    # `-v` prints one `path::name OUTCOME` line per test, so a run that dies in
    # collection reports no outcomes rather than looking quietly clean.
    outcomes = dict(
        re.findall(r"::(\w+) (PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)", completed.stdout)
    )
    return CheckerRun(
        frozenset(name for name, outcome in outcomes.items() if outcome == "PASSED"),
        frozenset(name for name, outcome in outcomes.items() if outcome != "PASSED"),
        completed.returncode,
        completed.stdout,
    )


def _variant(tmp_path: Path, name: str, mutate) -> Path:
    """One right-sized blueprint with a single thing wrong with it."""
    document = _load(RIGHT_SIZED)
    mutate(document)
    path = tmp_path / f"{name}.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


# --- Identity, rhythm, and the one deliverable --------------------------------


def test_s26_is_a_planning_session_with_the_exact_runbook_rhythm():
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")

    assert runbook.startswith("# S26 — Capstone Blueprint")
    assert task.startswith("# S26 Task Card — Capstone Blueprint")
    assert "**Role:** Project-primary planning lesson" in runbook
    assert "**Role:** Project-primary planning lesson" in task
    for anchor in (
        "0:00–0:05",
        "0:05–0:10",
        "0:10–0:18",
        "0:18–0:28",
        "0:28–0:35",
        "0:35–0:40",
        "0:40–0:44",
        "0:44–0:45",
    ):
        assert anchor in runbook, anchor
        assert anchor in task, anchor
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(31, 32))


def test_s26_ships_one_blueprint_and_no_implementation_scaffold():
    """The whole session is one student-owned file plus a menu and a gate."""
    shipped = sorted(
        path.relative_to(STUDENT_ROOT).as_posix()
        for path in STUDENT_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )

    assert shipped == [
        "capstone-blueprint.yaml",
        "examples/right-sized-blueprint.yaml",
        "examples/too-big-blueprint.yaml",
        "mechanic_menu.py",
        "task-card.md",
        "test_blueprint.py",
    ], shipped
    # S27 owns implementation. None of its shapes may be pre-built here.
    for drifted in (
        "starter.py",
        "project_data.py",
        "fixtures.py",
        "explorer-package",
        "project-record.md",
    ):
        assert not (STUDENT_ROOT / drifted).exists(), f"{drifted} is S27 work, not S26 work"
    assert not (S26_ROOT / "teacher-recovery-package").exists()
    assert not list(STUDENT_ROOT.rglob("manifest.yaml")), "S26 authors no package"


def test_s26_blueprint_is_entirely_unauthored_and_covers_every_gate_item():
    document = _load(BLUEPRINT_PATH)

    assert sorted(document) == [
        "build_plan",
        "integration",
        "mechanics",
        "project",
        "reflection",
        "risk",
        "world",
    ]
    assert sorted(document["project"]) == ["player_goal", "premise", "title"]
    assert sorted(document["integration"]) == [
        "connected_mechanics",
        "how_mechanics_connect",
        "observable_success",
    ]
    assert sorted(document["build_plan"]) == ["play_test_plan", "s27_target", "validation_plan"]
    assert sorted(document["risk"]) == ["biggest_risk", "fallback_if_time_runs_short"]
    assert sorted(document["reflection"]) == ["hardest_design_decision", "why_this_project"]
    assert sorted(document["world"]) == ["key_elements", "player_flow"]
    # The download makes no creative decision for the student.
    low, high = MENU["MECHANIC_LIMITS"]
    assert low <= len(document["mechanics"]) <= high
    assert all(entry["kind"] == PLACEHOLDER for entry in document["mechanics"])
    assert all(element["name"] == PLACEHOLDER for element in document["world"]["key_elements"])
    assert document["integration"]["connected_mechanics"] == [PLACEHOLDER, PLACEHOLDER]
    assert PLACEHOLDER in _read(BLUEPRINT_PATH)
    assert "python -m pytest -q lessons/sessions/s26/student/test_blueprint.py" in _read(
        BLUEPRINT_PATH
    )


# --- Engine honesty: the blueprint cannot invite unsupported behavior --------


def test_s26_mechanic_menu_matches_the_current_package_contracts():
    """Every offered mechanic is a field the loader really has."""
    from explore.packages.contribution_models import LoadedCharacter, LoadedWorldObject

    object_fields = set(LoadedWorldObject.__dataclass_fields__)
    character_fields = set(LoadedCharacter.__dataclass_fields__)

    assert set(SUPPORTED_KINDS) == {
        "response",
        "dialogue",
        "toggle",
        "toggle_style",
        "counter",
        "respond_to_toggle",
        "respond_to_two_toggles",
        "respond_to_either_toggle",
        "respond_to_counter",
        "respond_to_sequence",
    }
    for kind in ("toggle", "counter"):
        assert kind in object_fields, kind
    for kind in (
        "respond_to_toggle",
        "respond_to_two_toggles",
        "respond_to_either_toggle",
        "respond_to_counter",
        "respond_to_sequence",
    ):
        assert kind in character_fields, kind
    assert "toggle_style_id" in object_fields  # `toggle_style`
    assert {"when_near", "when_interacted"} <= object_fields  # `response`
    assert {"greeting", "conversation"} <= character_fields  # `dialogue`
    # Every entry says where it lives and what the student will have to author.
    for kind, entry in MENU["SUPPORTED_MECHANICS"].items():
        assert entry["lives_on"] in ("world object", "character"), kind
        assert entry["needs"].strip(), kind
        assert set(entry["reads"]) <= SUPPORTED_KINDS, kind


#: The producer/reader relation the package runtime really implements, checked
#: against the loader below. A reader appears here only where the loader would
#: accept a contribution of that kind pointed at an object of that kind.
RUNTIME_READS = {
    "response": (),
    "dialogue": (),
    "toggle": (),
    "toggle_style": (),
    "counter": (),
    "respond_to_toggle": ("toggle", "toggle_style"),
    "respond_to_two_toggles": ("toggle", "toggle_style"),
    "respond_to_either_toggle": ("toggle", "toggle_style"),
    "respond_to_counter": ("counter",),
    "respond_to_sequence": ("response", "toggle", "toggle_style", "counter"),
}


def test_s26_menu_reads_match_the_loader_producer_reader_relation():
    """The menu's `reads` is the loader's reference rule, not a resemblance."""
    assert {kind: tuple(entry["reads"]) for kind, entry in MENU["SUPPORTED_MECHANICS"].items()} == {
        kind: tuple(value) for kind, value in RUNTIME_READS.items()
    }

    loader_source = _read(PROJECT_ROOT / "explore" / "packages" / "loader.py")
    parser_source = _read(PROJECT_ROOT / "explore" / "packages" / "contribution_parser.py")
    # A styled switch is a switch: the parser fills the same `toggle` field from
    # a named style, so every switch-watcher the loader gates on toggle metadata
    # accepts a `toggle_style_id` object exactly as it accepts an inline one.
    assert "toggle = inline_toggle if inline_toggle is not None else style_toggle" in parser_source
    assert "must reference a world object with toggle metadata" in loader_source
    assert "must reference a world object with counter metadata" in loader_source
    # `toggle_style` reads nothing: reusing a named look is presentation, and
    # the parser refuses to let it sit beside an inline toggle at all.
    assert MENU["reads"]("toggle_style") == ()
    assert "cannot be combined with toggle" in parser_source
    # A sequence is gated on "a world object in this package" and nothing more.
    assert "respond_to_sequence" in loader_source


def test_s26_connectable_pairs_are_real_reader_and_producer_pairs():
    """A "connection" must be one mechanic that can genuinely read the other."""
    pairs = set(MENU["connectable_pairs"]())

    assert pairs == {
        tuple(sorted((reader, producer)))
        for reader, producers in RUNTIME_READS.items()
        for producer in producers
    }
    for expected in (
        ("counter", "respond_to_counter"),
        ("respond_to_toggle", "toggle"),
        ("respond_to_two_toggles", "toggle"),
        ("respond_to_either_toggle", "toggle"),
        ("respond_to_sequence", "response"),
        # A styled switch still needs somebody who watches it.
        ("respond_to_toggle", "toggle_style"),
        ("respond_to_two_toggles", "toggle_style"),
        ("respond_to_either_toggle", "toggle_style"),
    ):
        assert tuple(sorted(expected)) in pairs, expected
    # Two things that never look at each other are decorations, not a system.
    for absent in (
        ("counter", "dialogue"),
        ("counter", "toggle"),
        ("dialogue", "response"),
        ("respond_to_counter", "respond_to_toggle"),
        # Sharing one named look is styling, not one mechanic reading another.
        ("toggle", "toggle_style"),
        # `dialogue` lives on a character, so no sequence can point at it.
        ("dialogue", "respond_to_sequence"),
        ("respond_to_counter", "toggle_style"),
    ):
        assert tuple(sorted(absent)) not in pairs, absent
    assert not MENU["can_connect"]("toggle", "toggle_style")
    assert MENU["can_connect"]("toggle_style", "respond_to_toggle")
    assert not MENU["can_connect"]("counter", "counter")
    assert not MENU["can_connect"]("toggle_style", "toggle_style")
    assert not MENU["can_connect"]("counter", "not-a-mechanic")


def test_s26_documents_only_supported_mechanics_and_names_what_is_absent():
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    normalized = _normalized(runbook + task)

    for absent in (
        "no persistence across sessions",
        "no inventory",
        "no collision",
        "no arbitrary variable store",
        "no timers",
        "no networking or multiplayer",
        "no cross-package semantic reference",
        "no new mission or completion-rule",
    ):
        assert absent in _normalized(runbook), absent
    assert "the fix is the wording of the premise, not the engine" in normalized
    assert "do not extend the engine for a blueprint" in normalized
    assert "no new engine feature" in normalized
    # The task card names the absent features rather than staying silent about
    # them, and it offers a real mechanic in place of each tempting one.
    absent_section = task[task.index("What is **not** there") : task.index("For each mechanic")]
    for named in ("saved progress", "inventory", "health", "timers", "a second level"):
        assert named in absent_section, named
    substitutions = _normalized(absent_section)
    assert 'a toggle can mean "i have the key"' in substitutions
    assert 'a counter can mean "the lamp is nearly charged"' in substitutions


# --- The gate: red on download, green for a real design ----------------------


def _checker_test_names() -> tuple[str, ...]:
    tree = ast.parse(_read(CHECKER))
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )


def test_s26_gate_is_red_only_for_decisions_the_student_has_not_made():
    assert _checker_test_names() == BLUEPRINT_CHECKER_TESTS, _checker_test_names()

    run = _run_checker(CHECKER)

    assert run.returncode != 0, "the shipped download must start red"
    assert run.passed | run.failed == set(BLUEPRINT_CHECKER_TESTS), run.output
    assert run.passed == set(BLUEPRINT_GREEN_ON_DOWNLOAD), run.output
    assert (
        PLACEHOLDER in run.output
    ), "a failure must name the placeholder the student has to replace"


def test_s26_gate_goes_green_for_one_valid_right_sized_blueprint():
    """The shipped right-sized example is a complete, buildable design."""
    run = _run_checker(CHECKER, RIGHT_SIZED)

    assert run.returncode == 0, run.output
    assert run.passed == set(BLUEPRINT_CHECKER_TESTS), run.output

    document = _load(RIGHT_SIZED)
    kinds = [entry["kind"] for entry in document["mechanics"]]
    low, high = MENU["MECHANIC_LIMITS"]
    assert low <= len(kinds) <= high
    assert set(kinds) <= SUPPORTED_KINDS
    assert MENU["can_connect"](*document["integration"]["connected_mechanics"])
    assert PLACEHOLDER not in _read(RIGHT_SIZED)
    assert "not your project" in _read(RIGHT_SIZED)


def test_s26_gate_refuses_the_shipped_over_scoped_blueprint_by_name():
    """The too-big example is the class's reduction exercise, and it must fail."""
    run = _run_checker(CHECKER, TOO_BIG)
    document = _load(TOO_BIG)

    assert run.returncode != 0, run.output
    for refused in (
        "test_mechanics_are_two_to_four_supported_kinds",
        "test_world_has_two_to_four_key_elements",
        "test_player_flow_is_three_to_six_concrete_steps",
        "test_two_mechanics_are_really_connected",
        "test_s27_first_slice_is_bounded",
        "test_risk_and_fallback_are_named",
        "test_nothing_needs_a_feature_the_runtime_does_not_have",
    ):
        assert refused in run.failed, f"{refused} must refuse the over-scoped example\n{run.output}"
    # Every mechanic it names is real; the problem is how many, not which.
    assert {entry["kind"] for entry in document["mechanics"]} <= SUPPORTED_KINDS
    assert len(document["mechanics"]) > MENU["MECHANIC_LIMITS"][1]
    assert len(document["world"]["player_flow"]) > MENU["PLAYER_FLOW_LIMITS"][1]
    assert "reduce in this order" in _normalized(_read(TOO_BIG))


def test_s26_gate_refuses_six_specific_single_faults(tmp_path):
    """One fault at a time: the failure has to name the one thing that is wrong."""

    def too_many_mechanics(document):
        document["mechanics"].append(
            {"kind": "counter", "role_in_experience": "It counts the visitors who pass the pier."}
        )
        document["mechanics"].append(
            {
                "kind": "respond_to_counter",
                "role_in_experience": "A watcher compares that count with its goal.",
            }
        )

    def unsupported_mechanic(document):
        document["mechanics"][0]["kind"] = "inventory_slot"
        document["integration"]["connected_mechanics"] = [
            "inventory_slot",
            "respond_to_two_toggles",
        ]

    def missing_connection(document):
        document["integration"]["connected_mechanics"] = ["dialogue", "respond_to_two_toggles"]

    def unbounded_s27_target(document):
        document["build_plan"]["s27_target"] = "Build the whole game."

    def missing_s27_target(document):
        document["build_plan"]["s27_target"] = PLACEHOLDER

    def missing_fallback(document):
        document["risk"]["fallback_if_time_runs_short"] = PLACEHOLDER

    expected = {
        "too_many_mechanics": ("test_mechanics_are_two_to_four_supported_kinds", "mechanics"),
        "unsupported_mechanic": (
            "test_mechanics_are_two_to_four_supported_kinds",
            "inventory_slot",
        ),
        "missing_connection": ("test_two_mechanics_are_really_connected", "cannot connect"),
        "unbounded_s27_target": ("test_s27_first_slice_is_bounded", "whole game"),
        "missing_s27_target": (
            "test_s27_first_slice_is_bounded",
            "build_plan.s27_target is still blank",
        ),
        "missing_fallback": ("test_risk_and_fallback_are_named", "fallback_if_time_runs_short"),
    }
    mutations = {
        "too_many_mechanics": too_many_mechanics,
        "unsupported_mechanic": unsupported_mechanic,
        "missing_connection": missing_connection,
        "unbounded_s27_target": unbounded_s27_target,
        "missing_s27_target": missing_s27_target,
        "missing_fallback": missing_fallback,
    }

    for name, mutate in mutations.items():
        run = _run_checker(CHECKER, _variant(tmp_path, name, mutate))
        failing_test, quoted = expected[name]
        assert run.returncode != 0, f"{name} must be refused\n{run.output}"
        assert failing_test in run.failed, f"{name} must fail {failing_test}\n{run.output}"
        assert quoted in run.output, f"{name} must name {quoted!r} in its diagnostic\n{run.output}"


def test_s26_gate_judges_styled_switches_by_who_watches_them(tmp_path):
    """Sharing a look is not a connection; being watched is."""

    def design(*kinds: str):
        """One right-sized blueprint rebuilt around a named set of mechanics."""
        roles = {
            "toggle": "Each lantern is a switch the visitor flips to light the pier.",
            "toggle_style": (
                "Both lanterns share one named lantern look, so the pier reads as one harbour."
            ),
            "dialogue": "The harbour drum explains why the lanterns matter before anyone looks.",
            "counter": "A tally post counts how many lanterns the visitor has already tried.",
            "respond_to_toggle": "The keeper answers differently once the lantern is burning.",
            "respond_to_two_toggles": "The keeper holds the boat back until both lanterns are lit.",
            "respond_to_either_toggle": "The keeper starts loading as soon as one lantern is lit.",
            "respond_to_counter": "A watcher compares the tally post with the goal it was given.",
        }

        def mutate(document):
            document["mechanics"] = [
                {"kind": kind, "role_in_experience": roles[kind]} for kind in kinds
            ]
            document["integration"]["connected_mechanics"] = [kinds[0], kinds[1]]

        return mutate

    accepted = {
        # A styled switch is still a switch, so every switch-watcher can read it.
        "styled_toggle_and_respond_to_toggle": design(
            "toggle_style", "respond_to_toggle", "dialogue"
        ),
        "styled_toggle_and_two_toggles": design(
            "toggle_style", "respond_to_two_toggles", "dialogue"
        ),
        "styled_toggle_and_either_toggle": design(
            "toggle_style", "respond_to_either_toggle", "dialogue"
        ),
        # An unstyled switch with the same watcher stays accepted too.
        "plain_toggle_and_respond_to_toggle": design("toggle", "respond_to_toggle", "dialogue"),
    }
    for name, mutate in accepted.items():
        run = _run_checker(CHECKER, _variant(tmp_path, name, mutate))
        assert run.returncode == 0, f"{name} is a real system and must pass\n{run.output}"
        assert run.passed == set(BLUEPRINT_CHECKER_TESTS), run.output

    refused = {
        # The defect this test exists for: two switches that look alike and
        # nobody who notices either of them is decoration, not a system.
        "styled_toggle_with_nobody_watching": design("toggle", "toggle_style", "dialogue"),
        # Styling must not carry an otherwise unrelated pair over the gate.
        "styling_beside_an_unrelated_counter": design("toggle_style", "counter", "dialogue"),
        "styling_beside_an_unrelated_watcher": design(
            "toggle_style", "respond_to_counter", "counter"
        ),
        "two_watchers_that_never_meet": design(
            "respond_to_toggle", "respond_to_counter", "dialogue"
        ),
    }
    for name, mutate in refused.items():
        run = _run_checker(CHECKER, _variant(tmp_path, name, mutate))
        assert run.returncode != 0, f"{name} must be refused\n{run.output}"
        assert (
            "test_two_mechanics_are_really_connected" in run.failed
        ), f"{name} must fail the connection gate\n{run.output}"
        assert "cannot connect" in run.output, run.output
    # The refusal points at the menu, and the menu now offers the right pair in
    # place of the wrong one.
    run = _run_checker(
        CHECKER,
        _variant(tmp_path, "menu_in_message", refused["styled_toggle_with_nobody_watching"]),
    )
    assert "respond_to_toggle + toggle_style" in run.output, run.output
    assert ("toggle", "toggle_style") not in set(MENU["connectable_pairs"]())


def test_s26_gate_needs_neither_the_engine_nor_trail(tmp_path):
    """A blueprint review must work on a machine that cannot launch Trail."""
    imported = {
        node.module or ""
        for node in ast.walk(ast.parse(_read(CHECKER)))
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(ast.parse(_read(CHECKER)))
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert imported == {
        "__future__",
        "os",
        "sys",
        "pathlib",
        "pytest",
        "yaml",
        "mechanic_menu",
    }, imported
    # The student folder alone is enough: no repo imports, no package, no Trail.
    standalone = tmp_path / "student"
    shutil.copytree(STUDENT_ROOT, standalone)
    run = _run_checker(
        standalone / "test_blueprint.py", standalone / "examples" / "right-sized-blueprint.yaml"
    )
    assert run.returncode == 0, run.output
    # Nothing in the session asks a student to launch Trail.
    assert "explore-package" not in _read(STUDENT_ROOT / "task-card.md")


def test_s26_simulated_student_fills_a_blank_blueprint_and_the_gate_turns_green(tmp_path):
    """Walk the session: premise, mechanics, connection, flow, slice, risk."""
    standalone = tmp_path / "student"
    shutil.copytree(STUDENT_ROOT, standalone)
    blueprint_path = standalone / "capstone-blueprint.yaml"
    document = _load(blueprint_path)

    assert _run_checker(standalone / "test_blueprint.py").returncode != 0, "starts red"

    document["project"] = {
        "title": "The Quiet Greenhouse",
        "premise": (
            "A glass greenhouse on the roof of a school that stopped being watered when "
            "the caretaker left. The seedlings are still alive, and the light rig still works."
        ),
        "player_goal": "Warm all three seedling beds so the gardener will open the seed store.",
    }
    document["mechanics"] = [
        {
            "kind": "counter",
            "role_in_experience": "The light rig counts how often it was turned on the beds.",
        },
        {
            "kind": "respond_to_counter",
            "role_in_experience": "The gardener checks the rig before handing over any seeds.",
        },
        {
            "kind": "dialogue",
            "role_in_experience": "A watering can explains why the greenhouse went quiet.",
        },
    ]
    document["world"]["key_elements"] = [
        {"name": "Light Rig", "role": "The counter the visitor turns on the seedling beds."},
        {
            "name": "The Gardener",
            "role": "Reads the rig and opens the seed store when it reaches its goal.",
        },
        {"name": "Watering Can", "role": "Tells the visitor what happened to the greenhouse."},
    ]
    document["world"]["player_flow"] = [
        "The visitor talks to the watering can and hears about the caretaker.",
        "The visitor finds the light rig above the first seedling bed.",
        "The visitor turns the rig on each of the three beds in turn.",
        "The gardener notices the rig has reached its goal.",
        "The gardener opens the seed store and names the seedlings.",
    ]
    document["integration"] = {
        "connected_mechanics": ["counter", "respond_to_counter"],
        "how_mechanics_connect": (
            "The gardener compares the light rig's count with its goal, so every bed the "
            "visitor warms changes what the gardener is willing to say."
        ),
        "observable_success": "The gardener's line changes and the seed store is named as open.",
    }
    document["build_plan"] = {
        "s27_target": "Author the light rig with its counter and the gardener who reads it.",
        "validation_plan": "Run explore-package validate and read every diagnostic.",
        "play_test_plan": "Ask one classmate to reach the gardener's second line without hints.",
    }
    document["risk"] = {
        "biggest_risk": "Three seedling beds may be more than I can write good lines for.",
        "fallback_if_time_runs_short": "Cut to two beds and keep the rig and the gardener.",
    }
    document["reflection"] = {
        "why_this_project": "I liked that a greenhouse can be rescued by turning one thing on.",
        "hardest_design_decision": (
            "Whether the gardener or the rig should hold the goal; the gardener does, so "
            "the count means something to somebody."
        ),
    }
    blueprint_path.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    run = _run_checker(standalone / "test_blueprint.py")

    assert run.returncode == 0, run.output
    assert run.passed == set(BLUEPRINT_CHECKER_TESTS), run.output


# --- Ownership, pacing, reduction, and the S27 handoff -----------------------


def test_s26_student_owns_the_premise_and_the_teacher_may_only_narrow_it():
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    normalized = _normalized(runbook + task)

    assert "## Student-owned decisions — and what you must not decide for them" in runbook
    assert "may **not** invent the core premise" in runbook
    assert "the teacher does not" in normalized and "choose your premise" in normalized
    assert "## Degraded mode" in runbook
    assert "it does not replace their authorship" in normalized
    assert "not the default for a quiet student" in normalized
    assert "the premise is yours" in normalized
    # AI may critique scope and nothing else.
    assert "one bounded scope question only" in normalized
    for forbidden in (
        "invent your premise",
        "choose your mechanics",
        "write your player flow",
        "decide your s27 target",
    ):
        assert forbidden in normalized, forbidden


def test_s26_runbook_covers_pacing_failure_modes_reduction_and_the_cut_line():
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    normalized = _normalized(runbook)

    for heading in (
        "## Capstone purpose, and the S25/S27 bridge",
        "## The one deliverable",
        "## 45-minute runbook",
        "## Capstone size boundary",
        "## Supported mechanics only",
        '## What "connected" means',
        "## Too big versus right-sized",
        "## Paced scope reduction",
        "## Likely failure modes and recovery",
        "## Degraded mode",
        "## Blueprint completion gate",
        "## Teacher cut line",
        "## S26/S27 boundary",
        "## S27 handoff",
    ):
        assert heading in runbook, heading
    # The reduction ladder, in order, and what it must never do.
    for rung in (
        "reduce the number of key objects and characters",
        "reduce mechanics — four, then three, then two",
        "remove optional story branches",
        "keep one coherent interaction loop",
        "preserve the student's core premise",
    ):
        assert rung in runbook, rung
    assert "never solve scope by inventing an unsupported engine feature" in normalized
    assert "never let a student leave s26 without a usable s27 target" in normalized
    for failure_mode in (
        "no connection",
        "saved progress or an inventory",
        "started authoring yaml",
    ):
        assert failure_mode in normalized, failure_mode


def test_s26_names_the_nine_item_gate_and_the_bounded_s27_slice():
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    normalized = _normalized(runbook + task)

    for item in (
        "the premise is specific",
        "the player goal is observable",
        "two to four supported mechanics are selected",
        "at least two mechanics have a meaningful connection",
        "the player flow is concrete, three to six steps",
        "no unsupported runtime feature is required",
        "the s27 first slice is bounded and independently testable",
        "one major risk is named",
        "one fallback or simplification is named",
    ):
        assert item in normalized, item
    assert '"build the whole game" is not a target' in normalized
    # Every offered target has to be work S27 really does: S27 is a modular-core
    # Python session that writes no YAML, so none of these may name a file to
    # author or a package to validate.
    for example_target in (
        "define the modular core for your primary mechanic pair",
        "write the responsibilities and function contracts for one interaction",
        "implement and test the first helper your pair needs",
        "name the data shape your first interaction passes around",
    ):
        assert example_target in normalized, example_target
    for retired_target in (
        "author the first two world objects",
        "produce the first valid package slice",
    ):
        assert retired_target not in normalized, retired_target
    assert "never scores creativity" in normalized or "scores no creativity" in normalized
    assert (
        "requires\nno particular premise" in runbook
        or "requires a particular premise" in normalized
    )


def test_s26_makes_the_s25_to_s27_bridge_explicit_in_card_runbook_and_curriculum():
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    curriculum = " ".join(_read(PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md").split())
    normalized = _normalized(runbook + task)

    assert "i can build a small working system" in normalized
    assert "i can design a larger project before" in normalized
    assert "i can build the first working slice of my design" in normalized
    for document in (runbook, task):
        assert (
            "Playable Prototype → **Capstone Blueprint** → Core Build → Integration →" in document
        )
    assert (
        "Playable Prototype → Capstone Blueprint → Core Build → Integration → Review → Premiere."
        in curriculum
    )
    # The canonical milestone markers and the S25 contract stay untouched.
    assert "S20 is Milestone A" in _read(PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md")
    assert "S25, **Milestone B**" in _read(PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md")
    assert "The capstone build plan belongs to S26, not here." in curriculum
    assert "### S26 — Capstone Blueprint" in curriculum
    assert "**Project-primary planning session. Nothing is built.**" in curriculum
    assert "S26 introduces **no new programming syntax**" in curriculum


def test_s26_hands_s27_only_the_blueprint_and_a_target_s27_can_really_act_on():
    """The handoff must name what S26 produces and what S27 actually does."""
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    right_sized = _read(RIGHT_SIZED)
    s27_task = _read(MATERIALS_ROOT / "s27" / "student" / "task-card.md")
    s27_runbook = _read(MATERIALS_ROOT / "s27" / "teacher-runbook.md")
    s26_side = _normalized(runbook + task)
    s27_side = _normalized(s27_task + s27_runbook)

    # S26 says it hands over the blueprint and the target, and nothing more.
    assert "s26 hands s27 exactly two things" in s26_side
    assert (
        "s26 produces no responsibility map, no function contracts, and no project record"
        in s26_side
    )
    # S27 asks for exactly those two, and claims no inherited map or contracts.
    assert "capstone-blueprint.yaml" in s27_side
    assert "build_plan.s27_target" in s27_side
    assert "accepted s26 responsibility map" not in s27_side
    assert "your accepted s26 contracts" not in s27_side
    for derived in ("responsibility map", "function contracts"):
        assert derived in s27_side, derived
    assert "the responsibility map, the function contracts, and the project record" in s27_side
    assert "are all authored **here**" in s27_runbook

    # S27 writes Python, not YAML, and both sides now say the same thing.
    assert "s27 writes python, not yaml" in s26_side
    assert "do not create or overwrite yaml in s27" in s27_side
    for yaml_authoring in ("author the two lantern switch objects", "validate and play"):
        assert yaml_authoring not in _normalized(right_sized), yaml_authoring
    # The shipped example target is S27-shaped: a modular core, not a file.
    target = _normalized(_load(RIGHT_SIZED)["build_plan"]["s27_target"])
    assert "modular core" in target
    assert "function contracts" in target
    assert "tested helper" in target


def test_s26_curriculum_does_not_claim_every_later_session_reopens_the_blueprint():
    """S27 starts from the blueprint; S28–S30 continue from what came after."""
    curriculum = _read(PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md")
    normalized = _normalized(curriculum)

    assert "each of them\nstarts from `s26/student/capstone-blueprint.yaml`" not in curriculum
    assert "s27 starts directly from `s26/student/capstone-blueprint.yaml`" in normalized
    assert "s28–s30 continue from the capstone implementation and artifacts" in normalized
    assert "design of record rather than as each session's input" in normalized
    # And it names the handoff the same way the session materials do.
    assert "s26 produces no responsibility map, no function contracts, and no project record" in (
        normalized
    )
    assert "the package is authored in s28" in normalized


def test_s26_stays_on_the_planning_side_of_the_s27_boundary():
    runbook = _read(S26_ROOT / "teacher-runbook.md")
    task = _read(STUDENT_ROOT / "task-card.md")
    normalized = _normalized(runbook + task)

    assert "nothing is built today" in normalized
    assert "implementation starts in s27" in _normalized(
        _read(PROJECT_ROOT / "docs" / "curriculum-sessions-16-30.md")
    )
    # The one permitted experiment is labelled a probe and time-boxed.
    assert "## Optional feasibility probe" in task
    assert "not capstone implementation" in normalized
    assert "do not let it consume the session" in normalized
    assert "do not pre-build s27 deliverables" in normalized
    # S27's own materials are untouched by this session's refinement.
    assert (MATERIALS_ROOT / "s27" / "student" / "starter.py").is_file()
    assert (MATERIALS_ROOT / "s27" / "student" / "explorer-package" / "manifest.yaml").is_file()


def test_s26_git_close_stages_only_the_blueprint():
    task = _read(STUDENT_ROOT / "task-card.md")
    runbook = _read(S26_ROOT / "teacher-runbook.md")

    assert "git add lessons/sessions/s26/student/capstone-blueprint.yaml" in task
    for document in (task, runbook):
        assert "status → diff → staged diff → descriptive commit" in _normalized(document)
    assert "there is nothing else to stage" in _normalized(task)
    assert "ZIP path check" in task
    assert "ZIP classes" in runbook
