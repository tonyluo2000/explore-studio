"""Pinned network integration for the standalone student adventure template."""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
import venv
from pathlib import Path

import pytest

from scripts.provision_student_workspace import (
    COURSE_PLATFORM_COMMIT,
    provision_student_workspace,
)

PROJECT_ROOT = Path(__file__).parents[1]
TEMPLATE_REPOSITORY = "https://github.com/tonyluo2000/student-adventure-template.git"
TEMPLATE_COMMIT = "22afcc5c6f4f24ffd7e67d8ff70b0f8d49f5ff38"
PLATFORM_COMMIT = "70841376ddd58b82cd606d55d3703e86d8a4dccf"
PLATFORM_REQUIREMENT = (
    f"explore-studio @ git+https://github.com/tonyluo2000/explore-studio.git@{PLATFORM_COMMIT}"
)
EXPECTED_TREE = {
    ".github/workflows/smoke.yml": ("100644", "279de3cf1bbcf1fbaeb7374dbb9412f402320bab"),
    ".gitignore": ("100644", "2552a815a372d47fae5ab123733b695c35f260cc"),
    "LICENSES/EXPLORE-STUDIO-MIT.txt": (
        "100644",
        "3edd6fb4cfa8e55f8dd134d5b35ef19713454587",
    ),
    "README.md": ("100644", "984b5c2a7dab82b765b874da163b4057f6ecee27"),
    "dist/.gitkeep": ("100644", "8b137891791fe96927ad78e64b0aad7bded08bdc"),
    "explorer-package/manifest.yaml": (
        "100644",
        "6af5ff5f74df1fe41665aee3752087535278addd",
    ),
    "explorer-package/objects/beacon.yaml": (
        "100644",
        "1b4f8ce00ec7bd982130066fa27f0d7390d06766",
    ),
    "pyproject.toml": ("100644", "c20de5f00394febd249af144f72efcdc34d4a820"),
    "requirements-dev.txt": ("100644", "80173481441064b3633f6fe44ff8f1d168e9150d"),
    "tests/test_package.py": ("100644", "ef725f573828cbcf608e80ad3c7b4fb402ea2dae"),
}


def _run(command: list[str], *, cwd: Path, environment: dict[str, str]) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"command failed ({completed.returncode}): {command!r}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout


def _remote_tree(checkout: Path, environment: dict[str, str]) -> dict[str, tuple[str, str]]:
    listing = _run(["git", "ls-tree", "-r", "HEAD"], cwd=checkout, environment=environment)
    tree: dict[str, tuple[str, str]] = {}
    for line in listing.splitlines():
        metadata, filename = line.split("\t", 1)
        mode, object_type, object_id = metadata.split()
        assert object_type == "blob"
        tree[filename] = (mode, object_id)
    return tree


@pytest.mark.student_template_integration
@pytest.mark.skipif(
    os.environ.get("EXPLORE_STUDIO_RUN_TEMPLATE_INTEGRATION") != "1",
    reason="set EXPLORE_STUDIO_RUN_TEMPLATE_INTEGRATION=1 for the network integration",
)
@pytest.mark.skipif(os.name != "posix", reason="export v0.1 requires POSIX descriptors")
def test_pinned_standalone_template_contract(tmp_path: Path) -> None:
    checkout = tmp_path / "student-adventure-template"
    environment_root = tmp_path / "venv"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

    checkout.mkdir()
    _run(["git", "init", "--quiet"], cwd=checkout, environment=environment)
    _run(
        ["git", "remote", "add", "origin", TEMPLATE_REPOSITORY],
        cwd=checkout,
        environment=environment,
    )
    _run(
        ["git", "fetch", "--quiet", "--depth", "1", "origin", TEMPLATE_COMMIT],
        cwd=checkout,
        environment=environment,
    )
    _run(
        ["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"],
        cwd=checkout,
        environment=environment,
    )

    assert (
        _run(["git", "rev-parse", "HEAD"], cwd=checkout, environment=environment).strip()
        == TEMPLATE_COMMIT
    )
    assert _remote_tree(checkout, environment) == EXPECTED_TREE
    assert not (checkout / "explore").exists()
    assert not (checkout / "engine").exists()
    requirements = (checkout / "requirements-dev.txt").read_text(encoding="utf-8")
    project = (checkout / "pyproject.toml").read_text(encoding="utf-8")
    assert PLATFORM_REQUIREMENT in requirements.splitlines()
    assert 'dependencies = ["explore-studio==0.1.0"]' in project

    receipt = provision_student_workspace(checkout, PROJECT_ROOT)
    assert receipt["course_platform_commit"] == COURSE_PLATFORM_COMMIT
    assert not any(checkout.glob("lessons/sessions/s*/teacher-runbook.md"))
    assert len(tuple(checkout.glob("lessons/sessions/s*/student/task-card.md"))) == 30
    assert not (checkout / "lessons" / "sessions" / "s31").exists()

    venv.EnvBuilder(with_pip=True).create(environment_root)
    scripts = environment_root / "bin"
    python = scripts / "python"
    _run(
        [str(python), "-m", "pip", "install", "--quiet", "-r", "requirements-course.txt"],
        cwd=checkout,
        environment=environment,
    )
    imported_from = _run(
        [str(python), "-I", "-c", "import explore; print(explore.__file__)"],
        cwd=checkout,
        environment=environment,
    ).strip()
    assert str(PROJECT_ROOT) not in imported_from
    assert str(environment_root) in imported_from

    validation = _run(
        [str(scripts / "explore-package"), "validate", "explorer-package", "--json"],
        cwd=checkout,
        environment=environment,
    )
    assert json.loads(validation)["valid"] is True
    _run([str(python), "-m", "pytest", "-q"], cwd=checkout, environment=environment)

    assert (scripts / "explore-package").is_file()
    _run([str(scripts / "explore-package"), "--help"], cwd=checkout, environment=environment)
    starter_output = _run(
        [str(python), "lessons/sessions/s01/student/starter.py"],
        cwd=checkout,
        environment=environment,
    )
    assert starter_output.splitlines() == [
        "The crystal lantern glows beside the path.",
        "The river fountain sounds like quiet rain.",
        "Fern waits near the edge of the trail.",
    ]
    for package_id in (
        "nova-character",
        "forest-guide",
        "crystal-lantern",
        "river-fountain",
    ):
        _run(
            [
                str(scripts / "explore-package"),
                "validate",
                f"examples/explorer-packages/{package_id}",
            ],
            cwd=checkout,
            environment=environment,
        )

    trail_environment = environment.copy()
    trail_environment["SDL_VIDEODRIVER"] = "dummy"
    trail_environment["SDL_AUDIODRIVER"] = "dummy"
    trail_rehearsal = textwrap.dedent("""
        import threading
        import time

        import pygame

        from explore.packages.cli import main

        posted = []

        def close_trail():
            for _ in range(200):
                time.sleep(0.01)
                if pygame.display.get_init():
                    try:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                    except pygame.error:
                        continue
                    posted.append(True)
                    return

        closer = threading.Thread(target=close_trail)
        closer.start()
        result = main([
            "trail",
            "examples/explorer-packages/nova-character",
            "examples/explorer-packages/forest-guide",
            "examples/explorer-packages/crystal-lantern",
            "examples/explorer-packages/river-fountain",
            "--player", "nova-character:nova",
            "--mission-id", "visit-all-classroom-objects",
            "--name", "S01 Clean Workspace Rehearsal",
        ])
        closer.join()
        assert result == 0
        assert posted == [True]
        """)
    _run(
        [str(python), "-I", "-c", trail_rehearsal],
        cwd=checkout,
        environment=trail_environment,
    )

    destination = checkout / "dist" / "student-beacon-1.0.0.explorer-package.zip"
    exported = _run(
        [
            str(scripts / "explore-package"),
            "export",
            "explorer-package",
            "--output",
            str(destination),
            "--json",
        ],
        cwd=checkout,
        environment=environment,
    )
    assert json.loads(exported)["exported"] is True
    assert destination.is_file()
