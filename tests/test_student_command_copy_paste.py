"""Guard student-facing commands against copy-paste failures seen in class.

A Trail command that loses a continuation backslash runs one visual line at a
time: ``explore-package trail`` starts with no packages, each package path is
run as a command, and ``--player`` becomes "command not found". These checks
keep every multiline Trail command in course materials well formed, and keep the
computer check under its one real name.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[1]
QUICK_START = PROJECT_ROOT / "lessons" / "sessions" / "student-quick-start.md"
MARKDOWN_ROOTS = ("lessons", "classroom", "docs")
FENCE = re.compile(r"^\s*```")
TRAIL_COMMAND = "explore-package trail"


def markdown_files() -> list[Path]:
    return sorted(
        path for root in MARKDOWN_ROOTS for path in (PROJECT_ROOT / root).rglob("*.md")
    )


def fenced_blocks(text: str) -> list[tuple[int, list[str]]]:
    """Return (first line number, lines) for each fenced code block."""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    start = 0
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            if current is None:
                current, start = [], number + 1
            else:
                blocks.append((start, current))
                current = None
        elif current is not None:
            current.append(line)
    return blocks


def indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def trail_command_problems(start: int, lines: list[str]) -> list[str]:
    problems: list[str] = []
    command_indent: int | None = None
    for offset, line in enumerate(lines):
        number = start + offset
        if command_indent is None:
            if not line.strip().startswith(TRAIL_COMMAND):
                continue
            command_indent = indent(line)
        elif not line.strip():
            problems.append(f"line {number}: blank line inside a Trail command")
            command_indent = None
            continue
        if line.rstrip().endswith("\\"):
            if line != line.rstrip():
                problems.append(f"line {number}: whitespace after the continuation backslash")
            continue
        next_line = next((later for later in lines[offset + 1 :] if later.strip()), None)
        if next_line is not None and (
            next_line.strip().startswith("--") or indent(next_line) > command_indent
        ):
            problems.append(f"line {number}: Trail command line is missing its trailing backslash")
        command_indent = None
    if command_indent is not None:
        problems.append(f"line {start + len(lines) - 1}: Trail command ends with a dangling backslash")
    return problems


def trail_command_files() -> list[Path]:
    return [path for path in markdown_files() if TRAIL_COMMAND in path.read_text(encoding="utf-8")]


@pytest.mark.parametrize(
    "path", trail_command_files(), ids=lambda path: path.relative_to(PROJECT_ROOT).as_posix()
)
def test_multiline_trail_commands_keep_every_continuation_backslash(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    problems = [
        problem
        for start, lines in fenced_blocks(text)
        for problem in trail_command_problems(start, lines)
    ]

    assert not problems, problems


def test_guard_rejects_the_classroom_copy_paste_failure() -> None:
    malformed = [
        "explore-package trail",
        "  examples/explorer-packages/nova-character",
        "  --player \"nova-character:nova\"",
        "  --mission-id \"visit-all-classroom-objects\"",
    ]
    well_formed = [
        "explore-package trail \\",
        "  examples/explorer-packages/nova-character \\",
        "  --player \"nova-character:nova\"",
    ]

    assert trail_command_problems(1, malformed)
    assert trail_command_problems(1, [*well_formed[:-1], well_formed[-1] + " \\"])
    assert trail_command_problems(1, ["explore-package trail \\ ", "  pkg"])
    assert not trail_command_problems(1, well_formed)
    assert not trail_command_problems(1, ["explore-package trail pkg --player \"a:b\""])


def test_guard_scans_the_s01_to_s05_student_task_cards() -> None:
    scanned = {path.relative_to(PROJECT_ROOT).as_posix() for path in trail_command_files()}

    for session in ("s01", "s02", "s03", "s04", "s05"):
        assert f"lessons/sessions/{session}/student/task-card.md" in scanned


def test_quick_start_teaches_copying_the_whole_trail_command() -> None:
    quick_start = QUICK_START.read_text(encoding="utf-8")
    launch = quick_start[
        quick_start.index("## Launch, control, stop, and relaunch the Trail") :
        quick_start.index("## Accessibility and low-bandwidth route")
    ]

    for phrase in (
        "Copy the **entire** command block at once",
        "A backslash `\\` at the end of a line means",
        "continues on the\n  next line",
        "Do not press Enter after each line",
        "replace\n  each backslash and line break with a single space",
        "Ask the teacher for the one-line version",
        'explore-package trail package-one package-two --player "example:player"',
    ):
        assert phrase in launch, phrase
    assert "--player: command not found" in quick_start


def test_only_the_real_computer_check_name_is_used() -> None:
    tracked = subprocess.run(
        ["git", "grep", "-l", "check-my-setup", "--", ".", f":!{Path(__file__).relative_to(PROJECT_ROOT)}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert tracked.stdout == ""
    assert (PROJECT_ROOT / "check-my-computer.py").exists() or (
        PROJECT_ROOT / "course4teen-website" / "public" / "downloads" / "check-my-computer.py"
    ).exists()
