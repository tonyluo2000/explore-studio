from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from explore.packages.loader import load_explorer_package

MATERIALS_ROOT = Path(__file__).parents[1] / "lessons" / "sessions"
SESSION_MISSIONS = {
    "s01": "visit-all-classroom-objects",
    "s02": "create-a-classroom-object",
    "s03": "make-your-object-respond",
    "s04": "introduce-your-character",
    "s05": "write-a-short-conversation",
}
REQUIRED_RUNBOOK_SECTIONS = (
    "Learning objective",
    "Prerequisite",
    "45-minute runbook",
    "Student task",
    "prediction",
    "Deliberate debugging exercise",
    "Expected output and behavior",
    "Bounded AI assistance",
    "Git close",
    "Optional extension",
    "Teacher notes and answer key",
)
EXPECTED_STARTER_OUTPUTS = {
    "s01": (
        "The crystal lantern glows beside the path.\n"
        "The river fountain sounds like quiet rain.\n"
        "Fern waits near the edge of the trail.\n"
    ),
    "s02": "Moon Compass\n240 180\npurple\n",
    "s03": (
        "The Moon Compass needle begins to shimmer.\n"
        "You turn the Moon Compass toward a hidden trail!\n"
    ),
    "s04": (
        "Welcome to the Moonlit Trail, Ari!\n"
        "Welcome to the Moonlit Trail, Sam!\n"
    ),
    "s05": (
        "Guide: The moon compass is awake.\n"
        "Guide: Follow the silver lights home.\n"
        "3\n"
    ),
}


@pytest.mark.parametrize(("session", "mission_id"), SESSION_MISSIONS.items())
def test_session_runbook_uses_reusable_structure_and_canonical_mission(
    session: str, mission_id: str
) -> None:
    runbook = (MATERIALS_ROOT / session / "teacher-runbook.md").read_text(encoding="utf-8")

    assert mission_id in runbook
    assert "0:00–0:05" in runbook
    assert "0:42–0:45" in runbook
    assert "explain intent → predict → ask one bounded question → test →" in runbook
    assert "revise → explain accepted code" in runbook
    assert all(section.lower() in runbook.lower() for section in REQUIRED_RUNBOOK_SECTIONS)


@pytest.mark.parametrize(("session", "expected"), EXPECTED_STARTER_OUTPUTS.items())
def test_student_python_starter_is_runnable(
    session: str, expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    runpy.run_path(str(MATERIALS_ROOT / session / "student" / "starter.py"))

    assert capsys.readouterr().out == expected


@pytest.mark.parametrize("session", ("s02", "s03", "s04", "s05"))
def test_authored_session_package_is_valid(session: str) -> None:
    result = load_explorer_package(MATERIALS_ROOT / session / "student" / "explorer-package")

    assert result.is_loaded, result.all_issues
