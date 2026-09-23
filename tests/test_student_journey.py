"""My Explore Journey: a student-owned journal that Course Kit updates never touch."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from lessons.sessions.s30.student import journey_outline
from scripts.build_student_zip import ZIP_ROOT, build_student_zip
from scripts.make_my_world import WORKSPACE_NAME, make_my_world
from scripts.provision_student_workspace import provision_student_workspace

PROJECT_ROOT = Path(__file__).parents[1]
TEMPLATE_ROOT = PROJECT_ROOT / "classroom" / "my-world-template"
JOURNEY_TEMPLATE = TEMPLATE_ROOT / "journey.md"
S30_STUDENT_ROOT = PROJECT_ROOT / "lessons" / "sessions" / "s30" / "student"
HELPER = S30_STUDENT_ROOT / "journey_outline.py"
JOURNEY = Path("journey.md")
OUTLINE = Path("presentation-outline.md")
OWNED_FILES = (
    "README.md",
    "explorer.py",
    "companion.py",
    "projects/README.md",
    "projects/moon-compass/manifest.yaml",
    "projects/moon-compass/objects/compass.yaml",
)

#: Fictional entries only. No real student, place, or date.
FIRST_ENTRY = """## S02 — My Explorer and Companion
Date: September 26, 2026
Place: Home
Weather: Rainy
Explore-world location: Moon Compass Trail
### Today I built
My Explorer Card and my Companion Card.
### Python I learned
A variable holds a value.
### My favorite moment
The Moon Compass moved when I changed x.
### A problem I solved
A missing quote mark.
### My next idea
Give my companion a lantern.
"""
SECOND_ENTRY = """## S05 — Crystal Lantern
Date: October 24, 2026
Place: Prefer not to say
Weather: Don't know
Explore-world location: Crystal Lantern Trail
### Today I built
A lantern that toggles on and off.
### Python I learned
if and else choose between two paths.
### My favorite moment

### A problem I solved
Wrong indentation under the if.
### My next idea
Two lanterns that answer each other.
"""


def make_template(target: Path) -> Path:
    (target / ".git").mkdir(parents=True)
    (target / "explorer-package").mkdir()
    (target / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (target / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (target / "requirements-dev.txt").write_text("template pin\n", encoding="utf-8")
    (target / "explorer-package" / "manifest.yaml").write_text(
        'schema_version: "0.1"\n', encoding="utf-8"
    )
    return target


def provisioned_kit(root: Path) -> Path:
    kit = make_template(root / ZIP_ROOT)
    provision_student_workspace(kit, PROJECT_ROOT)
    return kit


def snapshot(workspace: Path) -> dict[str, bytes]:
    return {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in sorted(workspace.rglob("*"))
        if path.is_file()
    }


def journey_with(*entries: str) -> bytes:
    return (JOURNEY_TEMPLATE.read_text(encoding="utf-8") + "\n".join(entries)).encode("utf-8")


# --- Bootstrap persistence -------------------------------------------------------------


def test_new_workspace_receives_the_journey_seed(tmp_path):
    receipt = make_my_world(tmp_path / WORKSPACE_NAME, TEMPLATE_ROOT)

    journey = tmp_path / WORKSPACE_NAME / JOURNEY
    assert "journey.md" in receipt["created"]
    assert journey.read_bytes() == JOURNEY_TEMPLATE.read_bytes()


def test_rerun_keeps_an_edited_journey_byte_for_byte(tmp_path):
    workspace = tmp_path / WORKSPACE_NAME
    make_my_world(workspace, TEMPLATE_ROOT)
    edited = journey_with(FIRST_ENTRY)
    (workspace / JOURNEY).write_bytes(edited)

    receipt = make_my_world(workspace, TEMPLATE_ROOT)

    assert "journey.md" in receipt["kept"]
    assert receipt["created"] == []
    assert (workspace / JOURNEY).read_bytes() == edited


def test_journey_survives_course_kit_replacement_byte_for_byte(tmp_path):
    kit = provisioned_kit(tmp_path)
    command = [sys.executable, "make-my-world.py"]
    first = subprocess.run(command, cwd=kit, capture_output=True, text=True, check=True)
    assert "created  journey.md" in first.stdout
    workspace = tmp_path / WORKSPACE_NAME
    edited = journey_with(FIRST_ENTRY, SECOND_ENTRY)
    (workspace / JOURNEY).write_bytes(edited)
    before = snapshot(workspace)

    # A course update replaces/re-extracts the whole Course Kit folder.
    shutil.rmtree(kit)
    kit = provisioned_kit(tmp_path)
    rerun = subprocess.run(command, cwd=kit, capture_output=True, text=True, check=True)

    assert "kept     journey.md" in rerun.stdout
    assert "created  " not in rerun.stdout
    assert (workspace / JOURNEY).read_bytes() == edited
    assert snapshot(workspace) == before


def test_existing_workspace_without_a_journey_receives_one_and_nothing_else_changes(tmp_path):
    # A workspace made before the journal existed: same template minus journey.md.
    old_template = tmp_path / "old-template"
    shutil.copytree(TEMPLATE_ROOT, old_template)
    (old_template / JOURNEY).unlink()
    workspace = tmp_path / WORKSPACE_NAME
    make_my_world(workspace, old_template)
    assert not (workspace / JOURNEY).exists()
    (workspace / "explorer.py").write_text('explorer_name = "Juniper"\n', encoding="utf-8")
    (workspace / "projects" / "moon-compass" / "objects" / "compass.yaml").write_bytes(
        b'name: "My Moon Compass"\nx: 340\ny: 180\ncolor: "gold"\n'
    )
    (workspace / "projects" / "volcano.py").write_text("print('mine')\n", encoding="utf-8")
    before = snapshot(workspace)

    receipt = make_my_world(workspace, TEMPLATE_ROOT)

    assert receipt["created"] == ["journey.md"]
    assert sorted(receipt["kept"]) == sorted(OWNED_FILES)
    after = snapshot(workspace)
    assert after.pop("journey.md") == JOURNEY_TEMPLATE.read_bytes()
    assert after == before


def test_existing_journey_is_never_overwritten_even_by_a_changed_seed(tmp_path):
    workspace = tmp_path / WORKSPACE_NAME
    make_my_world(workspace, TEMPLATE_ROOT)
    mine = journey_with(FIRST_ENTRY)
    (workspace / JOURNEY).write_bytes(mine)
    newer_template = tmp_path / "newer-template"
    shutil.copytree(TEMPLATE_ROOT, newer_template)
    (newer_template / JOURNEY).write_text("# A newer seed\n", encoding="utf-8")

    receipt = make_my_world(workspace, newer_template)

    assert "journey.md" in receipt["kept"]
    assert (workspace / JOURNEY).read_bytes() == mine


# --- Seed content and privacy contract -------------------------------------------------


def normalized_seed() -> str:
    return " ".join(JOURNEY_TEMPLATE.read_text(encoding="utf-8").lower().split())


def test_seed_explains_ownership_and_the_never_overwrite_rule():
    seed = normalized_seed()

    assert "this file is mine" in seed
    assert "never replaces or edits it" in seed
    assert "course updates never change it" in seed


def test_seed_place_rule_is_general_and_optional_without_addresses_or_gps():
    seed = normalized_seed()

    assert "never write a street address" in seed
    assert "gps coordinates" in seed
    assert "prefer not to say" in seed
    assert "school name" in seed
    assert not re.search(r"\b\d{1,5} [a-z]+ (street|st\.|avenue|ave\.|road|rd\.)\b", seed)
    assert not re.search(r"\d+\.\d+°?\s*[ns],\s*-?\d+\.\d+", seed)


def test_seed_weather_is_optional_and_needs_no_service_or_network():
    seed = normalized_seed()

    assert "weather is optional" in seed
    assert "don't know" in seed
    assert "no app or website is needed" in seed
    assert "nothing here is uploaded" in seed
    for forbidden in ("http://", "https://", "sign in", "log in", "login", "account", "api"):
        assert forbidden not in seed, forbidden


def test_seed_separates_real_place_from_explore_world_location():
    seed = normalized_seed()

    assert "where *you* were in real life" in seed
    assert "where your *explorer* was" in seed


def test_seed_carries_a_copyable_blank_entry_with_every_field():
    seed = JOURNEY_TEMPLATE.read_text(encoding="utf-8")
    fenced = re.findall(r"```text\n(.*?)```", seed, re.DOTALL)

    assert len(fenced) == 2
    blank, example = fenced
    for label in journey_outline.FIELD_LABELS:
        assert f"{label}:" in blank
    for heading in journey_outline.SECTION_HEADINGS:
        assert f"### {heading}" in blank
        assert f"### {heading}" in example
    assert "S__" in blank
    # The example is labelled fictional and names only the class example world.
    assert "made-up example" in seed.lower()
    assert journey_outline.parse_journey(seed) == []


def test_seed_is_short_enough_for_ages_nine_to_thirteen():
    lines = JOURNEY_TEMPLATE.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 90
    assert all(len(line) <= 80 for line in lines)


# --- Course Kit and ZIP ----------------------------------------------------------------


def test_public_zip_ships_the_journey_seed_but_no_student_journal(tmp_path):
    archive_path = build_student_zip(tmp_path, PROJECT_ROOT)["archive"]
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        seed = archive.read(f"{ZIP_ROOT}/my-world-template/journey.md")

    assert seed == JOURNEY_TEMPLATE.read_bytes()
    assert f"{ZIP_ROOT}/lessons/sessions/s30/student/journey_outline.py" in names
    assert not any("/my-explore-world/" in name for name in names)
    assert not any(name.endswith("/presentation-outline.md") for name in names)


# --- S30 presentation outline helper ----------------------------------------------------


def workspace_with_journal(root: Path, *entries: str) -> Path:
    workspace = root / WORKSPACE_NAME
    make_my_world(workspace, TEMPLATE_ROOT)
    (workspace / JOURNEY).write_bytes(journey_with(*entries))
    return workspace


def test_outline_reads_the_journey_and_never_mutates_it(tmp_path):
    workspace = workspace_with_journal(tmp_path, FIRST_ENTRY, SECOND_ENTRY)
    journey_bytes = (workspace / JOURNEY).read_bytes()
    before = snapshot(workspace)

    receipt = journey_outline.prepare_outline(workspace)

    assert receipt["entries"] == 2
    assert (workspace / JOURNEY).read_bytes() == journey_bytes
    after = snapshot(workspace)
    assert after.pop(OUTLINE.as_posix())
    assert after == before


def test_outline_is_deterministic_and_replace_is_explicit(tmp_path):
    workspace = workspace_with_journal(tmp_path, FIRST_ENTRY, SECOND_ENTRY)
    journey_outline.prepare_outline(workspace)
    first = (workspace / OUTLINE).read_bytes()

    with pytest.raises(journey_outline.JourneyOutlineError, match="already exists"):
        journey_outline.prepare_outline(workspace)
    assert (workspace / OUTLINE).read_bytes() == first

    journey_outline.prepare_outline(workspace, replace=True)
    assert (workspace / OUTLINE).read_bytes() == first
    assert "/" not in first.decode("utf-8").split("`my-explore-world/journey.md`")[0]


def test_outline_keeps_entries_in_source_order_with_dates_and_both_places(tmp_path):
    workspace = workspace_with_journal(tmp_path, SECOND_ENTRY, FIRST_ENTRY)

    journey_outline.prepare_outline(workspace)
    outline = (workspace / OUTLINE).read_text(encoding="utf-8")

    assert outline.index("### S05 — Crystal Lantern") < outline.index(
        "### S02 — My Explorer and Companion"
    )
    assert "- Date: October 24, 2026" in outline
    assert "- Place: Prefer not to say" in outline
    assert "- Weather: Don't know" in outline
    assert "- Explore-world location: Crystal Lantern Trail" in outline
    assert "first entry, S05 — Crystal Lantern (October 24, 2026)" in outline
    assert "last entry, S02 — My Explorer and Companion (September 26, 2026)" in outline


def test_outline_surfaces_every_answer_under_its_question_and_leaves_the_choice_blank(tmp_path):
    workspace = workspace_with_journal(tmp_path, FIRST_ENTRY, SECOND_ENTRY)

    journey_outline.prepare_outline(workspace)
    outline = (workspace / OUTLINE).read_text(encoding="utf-8")

    for number, (question, _) in enumerate(journey_outline.PRESENTATION_QUESTIONS, start=1):
        assert f"### {number}. {question}" in outline
    problems = outline.split("### 3. What was a difficult problem I solved?")[1].split("### 4.")[0]
    assert "A missing quote mark." in problems
    assert "Wrong indentation under the if." in problems
    assert problems.index("A missing quote mark.") < problems.index("Wrong indentation")
    moments = outline.split("### 5. What was one memorable moment")[1].split("### 6.")[0]
    assert moments.count("\n- ") == 1  # the blank S05 favorite moment is not invented
    assert outline.count("My choice:\n\nWhat I will say:\n") == 6
    assert "I choose what to present" in outline
    for word in ("best", "most important", "impressive"):
        assert word not in outline.lower()


SCAFFOLD_PHRASES = (
    "Look at my first entry, ",
    "and my",
    "last entry, ",
    "What is different?",
    "I have one entry so far: ",
)


def test_outline_contains_only_the_students_own_words_plus_fixed_scaffolding(tmp_path):
    workspace = workspace_with_journal(tmp_path, FIRST_ENTRY, SECOND_ENTRY)
    journey_outline.prepare_outline(workspace)
    outline = (workspace / OUTLINE).read_text(encoding="utf-8")
    empty_workspace = workspace_with_journal(tmp_path / "empty")
    journey_outline.prepare_outline(empty_workspace)
    scaffold_lines = set((empty_workspace / OUTLINE).read_text(encoding="utf-8").splitlines())
    journal = (workspace / JOURNEY).read_text(encoding="utf-8")

    checked = 0
    for line in outline.splitlines():
        if not line.strip() or line in scaffold_lines:
            continue
        text = line.strip().removeprefix("### ").removeprefix("- ")
        for phrase in SCAFFOLD_PHRASES:
            text = text.replace(phrase, "|")
        for fixed in (*journey_outline.FIELD_LABELS, *journey_outline.SECTION_HEADINGS):
            text = text.replace(f"{fixed}:", "|")
        for fragment in re.split(r"[|():]", text):
            fragment = fragment.strip(" ,.")
            if fragment:
                assert fragment in journal, (line, fragment)
                checked += 1
    assert checked > 20


def test_outline_handles_an_empty_journal_and_a_missing_one_safely(tmp_path):
    empty = workspace_with_journal(tmp_path / "empty")
    receipt = journey_outline.prepare_outline(empty)
    outline = (empty / OUTLINE).read_text(encoding="utf-8")
    assert receipt["entries"] == 0
    assert "No entries were found" in outline
    assert "(none written yet)" in outline
    assert outline.count("### ") == 6

    missing = tmp_path / "missing" / WORKSPACE_NAME
    make_my_world(missing, TEMPLATE_ROOT)
    (missing / JOURNEY).unlink()
    with pytest.raises(journey_outline.JourneyOutlineError, match="cannot find journey.md"):
        journey_outline.prepare_outline(missing)
    assert not (missing / OUTLINE).exists()

    with pytest.raises(journey_outline.JourneyOutlineError, match="cannot find your"):
        journey_outline.prepare_outline(tmp_path / "nowhere")
    assert not (tmp_path / "nowhere").exists()


def test_outline_command_writes_only_inside_the_student_workspace(tmp_path):
    kit = provisioned_kit(tmp_path)
    subprocess.run(
        [sys.executable, "make-my-world.py"], cwd=kit, capture_output=True, text=True, check=True
    )
    workspace = tmp_path / WORKSPACE_NAME
    (workspace / JOURNEY).write_bytes(journey_with(FIRST_ENTRY))
    kit_before = snapshot(kit)
    journal_before = (workspace / JOURNEY).read_bytes()

    completed = subprocess.run(
        [sys.executable, "lessons/sessions/s30/student/journey_outline.py"],
        cwd=kit,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "1 entries, not changed" in completed.stdout
    assert (workspace / OUTLINE).is_file()
    assert (workspace / JOURNEY).read_bytes() == journal_before
    assert snapshot(kit) == kit_before
    assert sorted(path.name for path in tmp_path.iterdir()) == [ZIP_ROOT, WORKSPACE_NAME]


def test_outline_helper_needs_only_the_standard_library_and_no_ai_or_network():
    source = HELPER.read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])

    assert imported <= {"__future__", "argparse", "dataclasses", "pathlib", "sys"}
    for forbidden in ("anthropic", "openai", "requests", "urllib", "socket", "http"):
        assert forbidden not in source.lower(), forbidden


def test_outline_default_workspace_sits_next_to_the_course_kit():
    assert journey_outline.default_workspace_root() == PROJECT_ROOT.parent / WORKSPACE_NAME


# --- Course-wide documentation contract -----------------------------------------------


def test_workspace_docs_show_the_journey_and_its_contract():
    workspace_doc = (PROJECT_ROOT / "docs" / "classroom-student-workspace.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(workspace_doc.lower().split())

    assert "├── journey.md" in workspace_doc
    assert "overwrites, truncates, or regenerates it" in normalized
    assert "local-only by default" in normalized
    assert "never a street address" in normalized
    assert "prefer not to say" in normalized
    assert "weather` is an optional observation" in normalized
    assert "presentation-outline.md" in normalized
    assert "never modifies the journal" in normalized

    template_readme = (TEMPLATE_ROOT / "README.md").read_text(encoding="utf-8")
    assert "| `journey.md` |" in template_readme
    start_here = (PROJECT_ROOT / "classroom" / "START-HERE.md").read_text(encoding="utf-8")
    assert "`journey.md`" in start_here


def test_s30_materials_point_at_the_journey_without_ai_or_selection():
    task_card = (S30_STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join(task_card.lower().split())

    assert "python3 lessons/sessions/s30/student/journey_outline.py" in task_card
    assert "my-explore-world/journey.md" in task_card
    assert "without changing it" in normalized
    assert "not ai" in normalized
    assert "you choose which entries to present" in normalized
    for number, (question, _) in enumerate(journey_outline.PRESENTATION_QUESTIONS, start=1):
        assert f"{number}. {question}" in task_card
    checklist = (S30_STUDENT_ROOT / "premiere-checklist.md").read_text(encoding="utf-8")
    assert "presentation-outline.md" in checklist


def test_frozen_s01_and_s02_lesson_content_is_untouched_by_this_feature():
    for session in ("s01", "s02"):
        for path in (PROJECT_ROOT / "lessons" / "sessions" / session).rglob("*.md"):
            assert "journey.md" not in path.read_text(encoding="utf-8"), path
