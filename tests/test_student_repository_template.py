"""Independent bootstrap and smoke coverage for the student repository template."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import venv
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[1]
TEMPLATE_ROOT = PROJECT_ROOT / "templates" / "student-repository"
PLATFORM_COMMIT = "70841376ddd58b82cd606d55d3703e86d8a4dccf"
PLATFORM_REQUIREMENT = (
    f"explore-studio @ git+https://github.com/tonyluo2000/explore-studio.git@{PLATFORM_COMMIT}"
)


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


def _copy_platform_source(destination: Path) -> None:
    destination.mkdir()
    for filename in ("LICENSE", "README.md", "pyproject.toml"):
        shutil.copy2(PROJECT_ROOT / filename, destination / filename)
    for directory in ("engine", "explore"):
        shutil.copytree(
            PROJECT_ROOT / directory,
            destination / directory,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )


def test_template_contract_is_student_owned_and_canonically_pinned() -> None:
    requirements = (TEMPLATE_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    project = (TEMPLATE_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert PLATFORM_REQUIREMENT in requirements.splitlines()
    assert 'dependencies = ["explore-studio==0.1.0"]' in project
    assert (TEMPLATE_ROOT / "dist" / ".gitkeep").is_file()
    assert (TEMPLATE_ROOT / "LICENSES" / "EXPLORE-STUDIO-MIT.txt").is_file()
    assert (TEMPLATE_ROOT / "tests" / "test_package.py").is_file()
    assert not (TEMPLATE_ROOT / "explore").exists()
    assert not (TEMPLATE_ROOT / "engine").exists()


@pytest.mark.skipif(os.name != "posix", reason="export v0.1 requires POSIX descriptors")
def test_clean_template_runs_from_installed_platform_without_monorepo_imports(
    tmp_path: Path,
) -> None:
    platform_source = tmp_path / "platform-source"
    student_checkout = tmp_path / "student-repository"
    environment_root = tmp_path / "venv"
    _copy_platform_source(platform_source)
    shutil.copytree(
        TEMPLATE_ROOT,
        student_checkout,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment_root)

    scripts = environment_root / "bin"
    python = scripts / "python"
    pip = scripts / "pip"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

    _run(
        [str(pip), "install", "--no-deps", "--no-build-isolation", str(platform_source)],
        cwd=tmp_path,
        environment=environment,
    )
    _run(
        [
            str(pip),
            "install",
            "--no-deps",
            "--no-build-isolation",
            "--editable",
            f"{student_checkout}[dev]",
        ],
        cwd=tmp_path,
        environment=environment,
    )

    imported_from = _run(
        [str(python), "-I", "-c", "import explore; print(explore.__file__)"],
        cwd=student_checkout,
        environment=environment,
    ).strip()
    assert str(PROJECT_ROOT) not in imported_from
    assert str(environment_root) in imported_from

    validation = _run(
        [str(scripts / "explore-package"), "validate", "explorer-package", "--json"],
        cwd=student_checkout,
        environment=environment,
    )
    assert json.loads(validation)["valid"] is True

    _run(
        [str(python), "-m", "pytest", "-p", "no:cacheprovider"],
        cwd=student_checkout,
        environment=environment,
    )
    destination = student_checkout / "dist" / "student-beacon-1.0.0.explorer-package.zip"
    export = _run(
        [
            str(scripts / "explore-package"),
            "export",
            "explorer-package",
            "--output",
            str(destination),
            "--json",
        ],
        cwd=student_checkout,
        environment=environment,
    )
    assert json.loads(export)["exported"] is True
    assert destination.is_file()
