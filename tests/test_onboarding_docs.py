"""Semantic invariants for the active student setup and update documentation.

These check what the commands *do* (which folder a ``.venv`` is made in, where
lesson commands run, that the update flow moves the old kit aside before
unzipping) rather than pinning prose, so wording can keep improving.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[1]
GUIDE = PROJECT_ROOT / "docs" / "windows-wsl-setup.md"
PREPARE_PAGE = PROJECT_ROOT / "course4teen-website" / "app" / "students" / "prepare" / "page.tsx"
GUIDE_URL = "https://github.com/tonyluo2000/explore-studio/blob/main/docs/windows-wsl-setup.md"

#: Every active student-facing setup surface, plus the teacher docs that repeat
#: setup commands. Historical records and visual-proof notes are deliberately
#: not listed.
ACTIVE_DOCS = {
    "start-here": PROJECT_ROOT / "classroom" / "START-HERE.md",
    "quick-start": PROJECT_ROOT / "lessons" / "sessions" / "student-quick-start.md",
    "guide": GUIDE,
    "readiness": PROJECT_ROOT / "docs" / "computer-readiness.md",
    "workspace": PROJECT_ROOT / "docs" / "classroom-student-workspace.md",
    "world-readme": PROJECT_ROOT / "classroom" / "my-world-template" / "README.md",
    "preflight": PROJECT_ROOT / "docs" / "operations" / "classroom-preflight.md",
    "prepare-page": PREPARE_PAGE,
}
#: The surfaces a student reads to set up, check, and update.
SETUP_SURFACES = ("start-here", "quick-start", "guide", "prepare-page")

READY_COMMANDS = [
    "cd ~/explore-studio-course",
    "source .venv/bin/activate",
    "python3 check-my-computer.py",
]

#: The standalone pre-install check, run from wherever the browser saved it.
STANDALONE_CHECK = "python3 check-my-computer.py --computer-only"
#: The surfaces that teach the standalone pre-install check.
STANDALONE_SURFACES = ("guide", "prepare-page", "readiness")
WINDOWS_DOWNLOADS_COPY = re.compile(r"cp /mnt/c/Users/[^/\s]+/Downloads/check-my-computer\.py ~/?$")


def read(name: str) -> str:
    return ACTIVE_DOCS[name].read_text(encoding="utf-8")


def command_blocks(text: str) -> list[list[str]]:
    """Return each shell block's command lines, from Markdown or TSX code."""
    blocks = [
        textwrap.dedent(body)
        for _, body in re.findall(r"^( *)```console\n(.*?)^\1```", text, re.M | re.S)
    ]
    blocks += re.findall(r"<code>\{`(.*?)`\}</code>", text, re.S)
    blocks += re.findall(r"^const \w+ = `(.*?)`;", text, re.M | re.S)
    return [[line.strip() for line in block.splitlines() if line.strip()] for block in blocks]


def all_commands(name: str) -> list[list[str]]:
    return command_blocks(read(name))


def heading_anchors(text: str) -> set[str]:
    anchors = set()
    for heading in re.findall(r"^#{1,6} (.+)$", text, re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        anchors.add(slug)
    return anchors


@pytest.mark.parametrize("name", sorted(ACTIVE_DOCS))
def test_active_docs_use_the_canonical_course_kit_name_and_no_stale_folders(name):
    text = read(name)

    assert "explore-studio-course" in text
    assert "explorer-course" not in text
    assert "/home/student" not in text
    assert "home folder or Desktop" not in text


@pytest.mark.parametrize("name", SETUP_SURFACES)
def test_setup_surfaces_name_both_folders_and_the_windows_path(name):
    text = read(name)

    assert "~/explore-studio-course" in text
    assert "~/my-explore-world" in text
    assert "WSL" in text and "Ubuntu" in text


@pytest.mark.parametrize("name", sorted(ACTIVE_DOCS))
def test_every_venv_is_made_inside_the_course_kit(name):
    for block in all_commands(name):
        cwd = None
        for line in block:
            if line.startswith("cd "):
                cwd = line.split(maxsplit=1)[1]
            if re.match(r"python3? -m venv ", line):
                assert line.split()[-1] == ".venv", f"{name}: {line}"
                assert cwd in (None, "~/explore-studio-course"), f"{name}: venv made in {cwd}"
    text = read(name)
    assert "-m venv ~/.venv" not in text
    assert "my-explore-world/.venv" not in text


@pytest.mark.parametrize("name", sorted(ACTIVE_DOCS))
def test_no_command_runs_from_my_explore_world_or_the_windows_drive(name):
    for block in all_commands(name):
        for line in block:
            assert not re.match(r"cd \S*my-explore-world", line), f"{name}: {line}"
            assert not re.match(r"cd /mnt/", line), f"{name}: {line}"
            assert not re.match(r"unzip .*-d /mnt/", line), f"{name}: {line}"
            assert not (line.startswith("code ") and line.endswith("my-explore-world")), line


@pytest.mark.parametrize("name", SETUP_SURFACES)
def test_setup_surfaces_teach_the_am_i_ready_check(name):
    blocks = all_commands(name)

    assert any(block[:3] == READY_COMMANDS for block in blocks), f"{name} lacks the ready check"
    text = read(name)
    assert "(current)" in text
    assert "READY FOR EXPLORE STUDIO" in text


def test_the_prepare_page_ready_check_is_the_guides_checklist():
    page_blocks = all_commands("prepare-page")

    assert READY_COMMANDS in all_commands("guide")
    assert READY_COMMANDS in page_blocks


def standalone_runs(block: list[str]) -> list[tuple[str | None, bool]]:
    """Return ``(cwd, copied_home)`` for each standalone check run in a block."""
    cwd, copied_home, runs = None, False, []
    for line in block:
        if line.startswith("cd "):
            cwd = line.split(maxsplit=1)[1].rstrip("/") or None
        if WINDOWS_DOWNLOADS_COPY.match(line):
            copied_home = True
        if line == STANDALONE_CHECK:
            runs.append((cwd, copied_home))
    return runs


def standalone_blocks(name: str, cwd: str, copied_home: bool) -> list[list[str]]:
    return [block for block in all_commands(name) if (cwd, copied_home) in standalone_runs(block)]


@pytest.mark.parametrize("name", STANDALONE_SURFACES)
def test_standalone_check_on_windows_is_copied_home_from_windows_downloads(name):
    assert standalone_blocks(name, "~", copied_home=True), f"{name} lacks the WSL copy step"
    assert "YOUR-WINDOWS-NAME" in read(name)


@pytest.mark.parametrize("name", STANDALONE_SURFACES)
def test_standalone_check_on_a_mac_runs_from_downloads(name):
    assert standalone_blocks(name, "~/Downloads", copied_home=False), f"{name} lacks the Mac path"


@pytest.mark.parametrize("name", sorted(ACTIVE_DOCS))
def test_every_standalone_check_first_says_where_the_download_is(name):
    text = read(name)
    runs = [run for block in all_commands(name) for run in standalone_runs(block)]

    mentions = re.findall(re.escape(STANDALONE_CHECK) + r"(?! --)", text)
    assert len(mentions) == len(runs), f"{name} mentions the check outside a block"
    for cwd, copied_home in runs:
        assert (cwd == "~" and copied_home) or cwd == "~/Downloads", f"{name}: run from {cwd}"


def test_the_prepare_page_standalone_check_is_the_guides():
    guide_blocks = all_commands("guide")
    for cwd, copied_home in (("~", True), ("~/Downloads", False)):
        for block in standalone_blocks("prepare-page", cwd, copied_home):
            assert block in guide_blocks


def test_the_guide_update_flow_moves_the_old_kit_aside_and_starts_fresh():
    flow = [line for block in all_commands("guide") for line in block]

    def after(start: int, predicate) -> int:
        return next(i for i, line in enumerate(flow) if i > start and predicate(line))

    moved = flow.index("mv explore-studio-course explore-studio-course-old")
    unzipped = after(moved, lambda line: line.startswith("unzip "))
    fresh_venv = after(unzipped, lambda line: "-m venv .venv" in line)
    checked = after(fresh_venv, lambda line: "check-my-computer" in line)
    removed = flow.index("rm -rf ~/explore-studio-course-old")
    assert moved < unzipped < fresh_venv < checked < removed
    assert not any("rm" in line and "my-explore-world" in line for line in flow)


def test_the_guide_covers_the_whole_windows_path():
    guide = read("guide")
    commands = {line for block in all_commands("guide") for line in block}

    assert "wsl --install" in commands
    assert "sudo apt install -y python3 python3-venv python3-pip unzip" in commands
    assert "python3 --version" in commands
    assert any(line.startswith("cp /mnt/c/Users/") and "Downloads" in line for line in commands)
    assert "code ." in commands
    assert "WSL: Ubuntu" in guide
    assert "python -m pip install --force-reinstall -r requirements-student.txt" in commands
    assert "3.11" in guide and "24.04" in guide


def test_links_into_the_guide_point_at_real_sections():
    guide = GUIDE.read_text(encoding="utf-8")
    anchors = heading_anchors(guide)
    for name in ACTIVE_DOCS:
        for anchor in re.findall(r"windows-wsl-setup\.md#([\w-]+)", read(name)):
            assert anchor in anchors, f"{name} links to missing #{anchor}"
    for anchor in re.findall(r"\]\(#([\w-]+)\)", guide):
        assert anchor in anchors, f"guide links to missing #{anchor}"


def test_the_lesson_edit_risk_and_world_folder_rule_are_explicit():
    guide = " ".join(read("guide").split())

    assert "Lesson commands run from `~/explore-studio-course`" in guide
    assert "Your own work is saved in `~/my-explore-world`" in guide
    assert "lessons/sessions/" in guide and "replaced" in guide


# --- Website prepare page -------------------------------------------------------------


def test_prepare_page_is_a_current_hub_not_an_s01_page():
    page = read("prepare-page")

    assert 'title: "Prepare for class' in page
    assert "Prepare for S01" not in page and "ready for S01" not in page
    assert 'href="/downloads/explore-studio-course.zip"' in page
    assert GUIDE_URL in page
    assert GUIDE_URL.endswith(GUIDE.relative_to(PROJECT_ROOT).as_posix())
    assert "--computer-only" in page
    assert "courseKitVersion()" in page
    for anchor_id in ("ready", "folders", "download", "update", "help"):
        assert f'id="{anchor_id}"' in page
