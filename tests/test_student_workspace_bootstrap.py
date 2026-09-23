"""Course Kit vs Student Workspace: the bootstrap never overwrites student work."""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from explore.packages import load_explorer_package
from scripts.build_student_zip import (
    ZIP_ROOT,
    StudentZipError,
    assert_distribution_is_student_safe,
    build_student_zip,
    collect_members,
)
from scripts.make_my_world import (
    WORKSPACE_NAME,
    WorkspaceError,
    default_s02_package_seed_root,
    default_template_root,
    make_my_world,
)
from scripts.provision_student_workspace import provision_student_workspace

PROJECT_ROOT = Path(__file__).parents[1]
TEMPLATE_ROOT = PROJECT_ROOT / "classroom" / "my-world-template"
WORKSPACE_FILES = (
    "README.md",
    "explorer.py",
    "companion.py",
    "journey.md",
    "projects/README.md",
    "projects/moon-compass/manifest.yaml",
    "projects/moon-compass/objects/compass.yaml",
)
TEMPLATE_FILES = ("README.md", "explorer.py", "companion.py", "journey.md", "projects/README.md")
MOON_COMPASS = Path("projects/moon-compass/objects/compass.yaml")


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


def test_first_bootstrap_creates_every_personal_file(tmp_path):
    receipt = make_my_world(tmp_path / WORKSPACE_NAME, TEMPLATE_ROOT)

    assert sorted(receipt["created"]) == sorted(WORKSPACE_FILES)
    assert receipt["kept"] == []
    for relative in WORKSPACE_FILES:
        assert (tmp_path / WORKSPACE_NAME / relative).is_file()


def test_second_bootstrap_never_overwrites_edited_student_files(tmp_path):
    workspace = tmp_path / WORKSPACE_NAME
    make_my_world(workspace, TEMPLATE_ROOT)
    explorer = workspace / "explorer.py"
    explorer.write_text('explorer_name = "Juniper"\n', encoding="utf-8")
    (workspace / "projects" / "volcano.py").write_text("print('mine')\n", encoding="utf-8")

    receipt = make_my_world(workspace, TEMPLATE_ROOT)

    assert receipt["created"] == []
    assert sorted(receipt["kept"]) == sorted(WORKSPACE_FILES)
    assert explorer.read_text(encoding="utf-8") == 'explorer_name = "Juniper"\n'
    assert (workspace / "projects" / "volcano.py").read_text() == "print('mine')\n"


def test_rerun_restores_only_a_missing_file(tmp_path):
    workspace = tmp_path / WORKSPACE_NAME
    make_my_world(workspace, TEMPLATE_ROOT)
    (workspace / "explorer.py").write_text("# mine\n", encoding="utf-8")
    (workspace / "companion.py").unlink()

    receipt = make_my_world(workspace, TEMPLATE_ROOT)

    assert receipt["created"] == ["companion.py"]
    assert (workspace / "explorer.py").read_text(encoding="utf-8") == "# mine\n"


def test_bootstrap_refuses_a_workspace_inside_the_course_kit(tmp_path):
    kit = provisioned_kit(tmp_path)

    with pytest.raises(WorkspaceError, match="inside the course folder"):
        make_my_world(kit / WORKSPACE_NAME, TEMPLATE_ROOT)
    assert not (kit / WORKSPACE_NAME).exists()


def test_bootstrap_refuses_a_file_in_place_of_the_workspace(tmp_path):
    (tmp_path / WORKSPACE_NAME).write_text("not a folder", encoding="utf-8")

    with pytest.raises(WorkspaceError, match="not a folder"):
        make_my_world(tmp_path / WORKSPACE_NAME, TEMPLATE_ROOT)


def test_student_owned_s02_package_survives_rerun_and_reextracted_kit_byte_for_byte(tmp_path):
    kit = provisioned_kit(tmp_path)
    command = [sys.executable, "make-my-world.py"]

    first = subprocess.run(command, cwd=kit, capture_output=True, text=True, check=True)
    workspace = tmp_path / WORKSPACE_NAME
    assert "created  explorer.py" in first.stdout
    compass = workspace / MOON_COMPASS
    edited = b'name: "My Moon Compass"\nx: 340\ny: 180\ncolor: "gold"\n'
    compass.write_bytes(edited)

    rerun = subprocess.run(command, cwd=kit, capture_output=True, text=True, check=True)
    assert f"kept     {MOON_COMPASS.as_posix()}" in rerun.stdout
    assert compass.read_bytes() == edited

    # A course update replaces/re-extracts the whole Course Kit folder.
    shutil.rmtree(kit)
    kit = provisioned_kit(tmp_path)
    second = subprocess.run(command, cwd=kit, capture_output=True, text=True, check=True)

    assert f"kept     {MOON_COMPASS.as_posix()}" in second.stdout
    assert "created  " not in second.stdout
    assert compass.read_bytes() == edited
    loaded = load_explorer_package(workspace / "projects" / "moon-compass")
    assert loaded.is_loaded, loaded.all_issues
    assert loaded.package.world_objects[0].name == "My Moon Compass"


def test_kit_builder_never_absorbs_or_publishes_a_student_workspace(tmp_path):
    staged = provisioned_kit(tmp_path)
    make_my_world(tmp_path / "elsewhere", TEMPLATE_ROOT)
    shutil.copytree(tmp_path / "elsewhere", staged / WORKSPACE_NAME)

    members = collect_members(staged)

    assert not any(member.parts[0] == WORKSPACE_NAME for member in members)
    with pytest.raises(StudentZipError, match="must not contain my-explore-world"):
        assert_distribution_is_student_safe([*members, Path(WORKSPACE_NAME) / "explorer.py"])


def test_public_zip_ships_templates_and_bootstrap_but_no_personal_workspace(tmp_path):
    archive_path = build_student_zip(tmp_path, PROJECT_ROOT)["archive"]
    with zipfile.ZipFile(archive_path) as archive:
        paths = {name.split("/", 1)[1] for name in archive.namelist()}
        explorer = archive.read(f"{ZIP_ROOT}/my-world-template/explorer.py").decode()
        receipt = json.loads(archive.read(f"{ZIP_ROOT}/course-materials.json"))

    assert "make-my-world.py" in paths
    assert {f"my-world-template/{relative}" for relative in TEMPLATE_FILES} <= paths
    assert "lessons/sessions/s02/student/explorer-package/manifest.yaml" in paths
    assert "lessons/sessions/s02/student/explorer-package/objects/compass.yaml" in paths
    assert not any(path.startswith(f"{WORKSPACE_NAME}/") for path in paths)
    assert "lessons/sessions/s01/student/python-notes.md" in paths
    assert "lessons/sessions/s02/student/python-notes.md" in paths
    assert "lessons/sessions/s02/student/discovery.md" in paths
    assert "examples/explorer-packages/pixel-companion/manifest.yaml" in paths
    assert 'explorer_name = "TODO' in explorer
    assert "course_materials_source_commit" in receipt


@pytest.mark.parametrize("name", ("explorer.py", "companion.py"))
def test_templates_hold_placeholders_not_a_students_or_the_reference_answers(name: str):
    source = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    assignments = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
    ]

    assert assignments
    for node in assignments:
        assert isinstance(node.value.value, str)
        assert node.value.value.startswith("TODO"), ast.unparse(node)
    assert not re.search(r'^\w+ = "(Nova|Pixel)"', source, re.MULTILINE)


@pytest.mark.parametrize("name", ("explorer.py", "companion.py"))
def test_templates_run_as_plain_python(name: str, tmp_path):
    completed = subprocess.run(
        [sys.executable, str(TEMPLATE_ROOT / name)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "TODO" in completed.stdout


def test_companion_future_ability_is_planning_data_only():
    companion = (TEMPLATE_ROOT / "companion.py").read_text(encoding="utf-8")

    assert "future_ability = " in companion
    assert "cannot do it yet" in companion
    assert "def " not in companion


def test_ownership_templates_require_the_complete_student_choice_set():
    explorer = _assignment_names(TEMPLATE_ROOT / "explorer.py")
    companion = _assignment_names(TEMPLATE_ROOT / "companion.py")

    assert explorer == {
        "explorer_name",
        "looks_like",
        "personality",
        "favorite_subject",
    }
    assert companion == {
        "companion_name",
        "companion_kind",
        "personality",
        "specialty",
        "future_ability",
    }


def _assignment_names(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return names


def test_bootstrap_needs_only_the_standard_library_and_no_git():
    source = (PROJECT_ROOT / "scripts" / "make_my_world.py").read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])

    assert imported <= {"__future__", "argparse", "pathlib", "shutil", "sys"}


def test_default_template_is_found_from_a_source_checkout():
    assert default_template_root() == TEMPLATE_ROOT
    assert default_s02_package_seed_root() == (
        PROJECT_ROOT / "lessons" / "sessions" / "s02" / "student" / "explorer-package"
    )
