"""The documented Course Kit update never touches the student's own work.

Runs the exact ``mv``/``unzip``/``rm`` commands from
``docs/windows-wsl-setup.md`` against a temporary home folder holding an old
Course Kit and a student's ``my-explore-world`` with an edited journal, then
checks the world survives byte for byte, the new kit starts with no ``.venv``,
and the readiness check passes for a fresh install of the new kit.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.build_student_zip import build_student_zip
from scripts.check_computer_readiness import READY_BANNER, RuntimeFacts, overall_result, run_checks
from scripts.make_my_world import make_my_world
from scripts.provision_student_workspace import COURSE_PLATFORM_COMMIT
from tests.test_onboarding_docs import all_commands

pytestmark = pytest.mark.skipif(
    shutil.which("unzip") is None or shutil.which("bash") is None,
    reason="the documented update flow uses bash and unzip",
)

KIT = "explore-studio-course"
OLD_PIN = "0" * 40


def snapshot(folder: Path) -> dict[str, str]:
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def guide_block(containing: str) -> list[str]:
    return next(block for block in all_commands("guide") if containing in block)


def run_documented(lines: list[str], home: Path) -> None:
    environment = {**os.environ, "HOME": str(home)}
    subprocess.run(["bash", "-euc", "\n".join(lines)], check=True, env=environment, cwd=home)


@pytest.fixture(scope="module")
def new_kit_zip(tmp_path_factory) -> Path:
    return build_student_zip(tmp_path_factory.mktemp("zip"))["archive"]


def test_the_documented_update_preserves_my_explore_world(tmp_path, new_kit_zip):
    home = tmp_path / "home"
    home.mkdir()

    # An old Course Kit with a stale .venv and an unfinished in-kit lesson edit.
    shutil.copy(new_kit_zip, home / f"{KIT}.zip")
    run_documented([f"cd ~ && unzip -q {KIT}.zip && rm {KIT}.zip"], home)
    old_kit = home / KIT
    (old_kit / ".venv" / "bin").mkdir(parents=True)
    (old_kit / ".venv" / "old-pin").write_text(OLD_PIN, encoding="utf-8")
    (old_kit / "lessons" / "sessions" / "s03" / "student" / "starter.py").write_text(
        "# my unfinished lesson edit\n", encoding="utf-8"
    )

    # The student's own world, made by the kit and then edited.
    make_my_world(
        home / "my-explore-world",
        template_root=old_kit / "my-world-template",
        package_seed_root=old_kit / "lessons/sessions/s02/student/explorer-package",
    )
    world = home / "my-explore-world"
    (world / "journey.md").write_text("# My Explore Journey\n\nS03: the compass!\n", "utf-8")
    (world / "explorer.py").write_text('name = "Stanley"\n', encoding="utf-8")
    before = snapshot(world)

    # The new ZIP is copied home (guide step 3), then steps 4 and 6 run verbatim.
    shutil.copy(new_kit_zip, home / f"{KIT}.zip")
    run_documented(guide_block("mv explore-studio-course explore-studio-course-old"), home)

    new_kit = home / KIT
    assert (home / f"{KIT}-old" / ".venv" / "old-pin").is_file()
    assert not (new_kit / ".venv").exists(), "the new Course Kit must start with a fresh .venv"
    assert "unfinished lesson edit" not in (
        new_kit / "lessons" / "sessions" / "s03" / "student" / "starter.py"
    ).read_text(encoding="utf-8")
    assert snapshot(world) == before

    # Re-running the world command from the new kit keeps every existing file.
    receipt = make_my_world(
        world,
        template_root=new_kit / "my-world-template",
        package_seed_root=new_kit / "lessons/sessions/s02/student/explorer-package",
    )
    assert receipt["created"] == []
    assert snapshot(world) == before

    # A fresh .venv with the new kit's pinned tools is READY.
    fresh = new_kit / ".venv"
    fresh.mkdir()
    results = run_checks(
        workspace=new_kit,
        home=home,
        system="Darwin",
        wsl=False,
        version=(3, 12, 3),
        environ={},
        total_memory_bytes=16 * 1000**3,
        free_disk_bytes=50 * 1000**3,
        trail_launcher=lambda: ("ok", "a test window opened and closed"),
        runtime=RuntimeFacts(
            prefix=fresh,
            in_venv=True,
            platform_installed=True,
            installed_commit=COURSE_PLATFORM_COMMIT,
            launcher_prefix=fresh,
            trail_dependency_installed=True,
        ),
    )
    assert overall_result(results) == READY_BANNER

    # Only after READY: the documented removal of the old copy.
    run_documented(guide_block("rm -rf ~/explore-studio-course-old"), home)
    assert not (home / f"{KIT}-old").exists()
    assert not (home / f"{KIT}.zip").exists()
    assert snapshot(world) == before
