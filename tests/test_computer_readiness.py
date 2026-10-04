from __future__ import annotations

import io
import json
import re
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.check_computer_readiness import (
    COMPUTER_ONLY_BANNER,
    FORCE_REINSTALL,
    HELP,
    HELP_BANNER,
    MINIMUM_FREE_DISK_BYTES,
    MINIMUM_MEMORY_BYTES,
    NOTE,
    OK,
    READY_BANNER,
    RuntimeFacts,
    check_course_folder,
    check_disk_space,
    check_display,
    check_memory,
    check_operating_system,
    check_python,
    check_student_world,
    commit_from_direct_url,
    format_report,
    main,
    overall_result,
    read_expected_pin,
    run_checks,
    shorten_home,
)
from scripts.provision_student_workspace import COURSE_PLATFORM_COMMIT

PROJECT_ROOT = Path(__file__).parents[1]
PINNED = "a" * 40
OLDER = "b" * 40
MATERIALS = "c" * 40

#: The exact form pip writes for the course's HTTPS-archive install (PEP 610),
#: copied from a real ``pip install -r requirements-student.txt``.
_REAL_ARCHIVE_HASH = "da02807368e16d22d85c0d9b46a1c6428a643cbaf89d955aa330c6ee2ae15d35"
REAL_ARCHIVE_DIRECT_URL = json.dumps(
    {
        "archive_info": {
            "hash": f"sha256={_REAL_ARCHIVE_HASH}",
            "hashes": {"sha256": _REAL_ARCHIVE_HASH},
        },
        "url": "https://github.com/tonyluo2000/explore-studio/archive/"
        f"{COURSE_PLATFORM_COMMIT}.tar.gz",
    }
)

COMPUTER = {
    "system": "Darwin",
    "wsl": False,
    "version": (3, 12, 3),
    "environ": {},
    "total_memory_bytes": MINIMUM_MEMORY_BYTES,
    "free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
}


def trail_opened() -> tuple[str, str]:
    return "ok", "a test window opened and closed"


def trail_failed() -> tuple[str, str]:
    return "failed", "a window could not open (error)"


def make_kit(root: Path, *, pin: str = PINNED, git_managed: bool = False) -> Path:
    """Write the files that make ``root`` a Course Kit, pinned like the real one."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "START-HERE.md").write_text("# Start Here\n", encoding="utf-8")
    (root / "course-materials.json").write_text(
        json.dumps({"course_materials_source_commit": MATERIALS, "course_platform_commit": pin}),
        encoding="utf-8",
    )
    (root / "requirements-student.txt").write_text(
        "# Explore Studio — student course tools\npytest==8.3.3\n"
        f"explore-studio @ https://github.com/tonyluo2000/explore-studio/archive/{pin}.tar.gz\n",
        encoding="utf-8",
    )
    if git_managed:
        (root / "requirements-course.txt").write_text("-e .[dev]\n", encoding="utf-8")
    (root / ".venv").mkdir(exist_ok=True)
    return root


def runtime_for(kit: Path, **overrides) -> RuntimeFacts:
    """Facts for this kit's own active .venv with the pinned tools installed."""
    facts = RuntimeFacts(
        prefix=kit / ".venv",
        in_venv=True,
        platform_installed=True,
        installed_commit=PINNED,
        launcher_prefix=kit / ".venv",
        trail_dependency_installed=True,
    )
    return replace(facts, **overrides)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "home"


@pytest.fixture
def kit(home: Path) -> Path:
    return make_kit(home / "explore-studio-course")


def results_for(workspace: Path, home: Path, runtime: RuntimeFacts | None = None, **overrides):
    settings = {**COMPUTER, **overrides}
    settings.setdefault("trail_launcher", trail_opened)
    if runtime is None:
        runtime = runtime_for(workspace)
    return run_checks(workspace=workspace, home=home, runtime=runtime, **settings)


def named(results, name):
    return next(result for result in results if result.name == name)


def summary_lines(report: str) -> list[str]:
    return report.split("\nSummary\n", 1)[1].split("\n\n", 1)[0].splitlines()


# --- 1, 9: the one READY path -------------------------------------------------


def test_correct_kit_active_venv_and_current_tools_are_ready(kit, home):
    results = results_for(kit, home)

    assert overall_result(results) == READY_BANNER
    report = format_report(results)
    assert summary_lines(report) == [
        "  Python: 3.12.3",
        "  Course folder: OK",
        "  Virtual environment: .venv",
        f"  Course tools: {PINNED[:7]} (current)",
        "  Trail dependency: OK",
    ]
    assert report.rstrip().splitlines()[-3] == READY_BANNER


# --- 2: wrong folder ----------------------------------------------------------


@pytest.mark.parametrize("where", ["home", "world", "lessons"])
def test_running_outside_the_kit_root_is_wrong_folder(kit, home, where):
    workspace = {
        "home": home,
        "world": home / "my-explore-world",
        "lessons": kit / "lessons",
    }[where]
    workspace.mkdir(parents=True, exist_ok=True)

    results = results_for(workspace, home, runtime=runtime_for(kit))
    folder = named(results, "Course folder")
    assert folder.status == HELP
    assert folder.detail.startswith("WRONG FOLDER")
    assert "cd ~/explore-studio-course" in folder.advice
    assert overall_result(results) == HELP_BANNER
    if where == "world":
        assert "your world folder" in folder.detail


def test_the_kit_belongs_in_exactly_home_explore_studio_course(home):
    elsewhere = make_kit(home / "Desktop" / "explore-studio-course")
    moved = check_course_folder(elsewhere, False, home)
    assert moved.status == HELP
    assert "~/explore-studio-course" in moved.advice and "my-explore-world" in moved.advice

    downloads = make_kit(home / "Downloads" / "explore-studio-course")
    assert "Downloads" in check_course_folder(downloads, False, home).detail

    nested = make_kit(home / "explore-studio-course" / "explore-studio-course")
    assert check_course_folder(nested, False, home).status == HELP
    assert check_course_folder(nested.parent, False, home).status == HELP


def test_a_git_managed_course_folder_may_use_another_name(home):
    repository = make_kit(home / "student-course-repo", git_managed=True)

    assert check_course_folder(repository, False, home).status == OK


def test_a_course_kit_on_the_windows_drive_needs_help(monkeypatch, home):
    on_windows_drive = Path("/mnt/c/Users/student/explore-studio-course")
    monkeypatch.setattr(
        "scripts.check_computer_readiness.is_course_kit", lambda path: path == on_windows_drive
    )

    result = check_course_folder(on_windows_drive, True, home)
    assert result.status == HELP
    assert "/mnt/c" in result.advice


# --- 3, 4: the virtual environment ---------------------------------------------


def test_an_inactive_venv_is_not_ready(kit, home):
    results = results_for(kit, home, runtime=runtime_for(kit, in_venv=False, prefix=Path("/usr")))

    venv = named(results, "Virtual environment")
    assert venv.status == HELP
    assert venv.detail.startswith("VENV NOT ACTIVE")
    assert "source .venv/bin/activate" in venv.advice
    assert overall_result(results) == HELP_BANNER
    assert named(results, "Course tools").summary == "not checked"


def test_an_inactive_venv_without_a_venv_says_how_to_make_one(kit, home):
    (kit / ".venv").rmdir()
    results = results_for(kit, home, runtime=runtime_for(kit, in_venv=False, prefix=Path("/usr")))

    assert "python3 -m venv .venv" in named(results, "Virtual environment").advice


@pytest.mark.parametrize("wrong", ["home-venv", "other-project"])
def test_a_venv_outside_the_course_kit_is_in_the_wrong_place(kit, home, wrong):
    prefix = {"home-venv": home / ".venv", "other-project": home / "other" / ".venv"}[wrong]
    prefix.mkdir(parents=True)

    results = results_for(
        kit, home, runtime=runtime_for(kit, prefix=prefix, launcher_prefix=prefix)
    )
    venv = named(results, "Virtual environment")
    assert venv.detail.startswith("VENV IN WRONG PLACE")
    assert "deactivate" in venv.advice
    assert overall_result(results) == HELP_BANNER


def test_a_moved_or_copied_venv_is_in_the_wrong_place(kit, home):
    results = results_for(kit, home, runtime=runtime_for(kit, launcher_prefix=Path("/old/.venv")))

    venv = named(results, "Virtual environment")
    assert venv.detail.startswith("VENV IN WRONG PLACE")
    assert "rm -rf .venv" in venv.advice
    assert overall_result(results) == HELP_BANNER


# --- 5: Python version --------------------------------------------------------


def test_python_311_is_the_minimum_and_older_python_is_never_ready(kit, home):
    assert check_python((3, 11, 0)).status == OK
    assert check_python((3, 12, 5)).status == OK
    too_old = check_python((3, 10, 12))
    assert too_old.status == HELP
    assert "24.04" in too_old.advice and "3.10" in too_old.advice

    results = results_for(kit, home, version=(3, 10, 12))
    assert overall_result(results) == HELP_BANNER
    assert "  Python: 3.10.12 (TOO OLD, needs 3.11+)" in summary_lines(format_report(results))


# --- 6, 7, 8: course tools -----------------------------------------------------


def test_missing_course_tools_are_not_installed(kit, home):
    results = results_for(
        kit, home, runtime=runtime_for(kit, platform_installed=False, installed_commit=None)
    )

    tools = named(results, "Course tools")
    assert tools.detail.startswith("COURSE TOOLS NOT INSTALLED")
    assert "python -m pip install -r requirements-student.txt" in tools.advice
    assert overall_result(results) == HELP_BANNER


def test_tools_without_a_version_record_are_not_installed_from_this_kit(kit, home):
    results = results_for(kit, home, runtime=runtime_for(kit, installed_commit=None))

    tools = named(results, "Course tools")
    assert tools.detail.startswith("COURSE TOOLS NOT INSTALLED")
    assert FORCE_REINSTALL in tools.advice


def test_missing_pygame_is_not_ready_even_with_the_tools_installed(kit, home):
    results = results_for(kit, home, runtime=runtime_for(kit, trail_dependency_installed=False))

    dependency = named(results, "Trail dependency")
    assert dependency.status == HELP
    assert "pygame" in dependency.detail
    assert overall_result(results) == HELP_BANNER
    assert "Trail window opens and closes" not in {result.name for result in results}


def test_stale_course_tools_are_out_of_date_with_both_short_shas(kit, home):
    results = results_for(kit, home, runtime=runtime_for(kit, installed_commit=OLDER))

    tools = named(results, "Course tools")
    assert tools.status == HELP
    assert tools.detail.startswith("COURSE TOOLS OUT OF DATE")
    assert OLDER[:7] in tools.detail and PINNED[:7] in tools.detail
    assert FORCE_REINSTALL in tools.advice
    assert overall_result(results) == HELP_BANNER
    expected = (
        f"  Course tools: COURSE TOOLS OUT OF DATE (installed {OLDER[:7]}, needs {PINNED[:7]})"
    )
    assert expected in summary_lines(format_report(results))


def test_a_failed_trail_window_is_not_ready(kit, home):
    results = results_for(kit, home, trail_launcher=trail_failed)

    assert overall_result(results) == HELP_BANNER


# --- 10: READY invariant -------------------------------------------------------


BROKEN = {
    "wrong folder": {"workspace": "home"},
    "venv inactive": {"runtime": {"in_venv": False, "prefix": Path("/usr")}},
    "venv elsewhere": {"runtime": {"prefix": Path("/elsewhere/.venv")}},
    "tools missing": {"runtime": {"platform_installed": False, "installed_commit": None}},
    "tools stale": {"runtime": {"installed_commit": OLDER}},
    "pygame missing": {"runtime": {"trail_dependency_installed": False}},
    "old python": {"version": (3, 10, 12)},
    "windows": {"system": "Windows"},
    "low memory": {"total_memory_bytes": 1},
}


@pytest.mark.parametrize("problem", sorted(BROKEN))
def test_a_blocking_failure_never_prints_ready(kit, home, problem):
    change = dict(BROKEN[problem])
    workspace = home if change.pop("workspace", None) else kit
    runtime = runtime_for(kit, **change.pop("runtime", {}))

    results = results_for(workspace, home, runtime=runtime, **change)
    report = format_report(results)
    assert overall_result(results) == HELP_BANNER
    assert "READY" not in report.replace(HELP_BANNER, "")


def test_notes_alone_can_never_stand_in_for_a_blocking_check(kit, home):
    results = [result for result in results_for(kit, home) if result.name != "Course tools"]

    assert overall_result(results) == HELP_BANNER


# --- 11: offline -----------------------------------------------------------------


def test_the_full_check_never_touches_the_network(kit, home, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the readiness check must not open a network connection")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)

    results = results_for(kit, home)
    assert overall_result(results) == READY_BANNER
    assert "Internet connection" not in {result.name for result in results}


# --- 12, 13: pin parsing -----------------------------------------------------------


def test_expected_pin_is_parsed_from_the_real_student_requirements(tmp_path):
    student_pin = (PROJECT_ROOT / "classroom" / "requirements-student.txt").read_text("utf-8")
    (tmp_path / "requirements-student.txt").write_text(student_pin, encoding="utf-8")

    assert read_expected_pin(tmp_path) == COURSE_PLATFORM_COMMIT


def test_expected_pin_falls_back_to_the_git_course_requirements(tmp_path):
    course_pin = (PROJECT_ROOT / "classroom" / "requirements-course.txt").read_text("utf-8")
    (tmp_path / "requirements-course.txt").write_text(course_pin, encoding="utf-8")

    assert read_expected_pin(tmp_path) == COURSE_PLATFORM_COMMIT
    assert read_expected_pin(tmp_path / "missing") is None


def test_installed_commit_is_read_from_real_pip_install_records():
    assert commit_from_direct_url(REAL_ARCHIVE_DIRECT_URL) == COURSE_PLATFORM_COMMIT
    git_install = {
        "url": "https://github.com/tonyluo2000/explore-studio.git",
        "vcs_info": {"vcs": "git", "commit_id": OLDER, "requested_revision": OLDER},
    }
    assert commit_from_direct_url(json.dumps(git_install)) == OLDER
    editable = {"url": f"file:///src/{PINNED}", "dir_info": {"editable": True}}
    assert commit_from_direct_url(json.dumps(editable)) is None
    assert commit_from_direct_url(None) is None
    assert commit_from_direct_url("not json") is None


# --- Course Kit facts -------------------------------------------------------------


def test_the_kit_version_is_printed_short(kit, home):
    version = named(results_for(kit, home), "Course Kit version")

    assert version.status == OK
    assert version.detail.startswith(MATERIALS[:7])
    assert MATERIALS not in version.detail


def test_my_explore_world_belongs_beside_the_kit_never_inside(kit, home):
    assert check_student_world(kit).status == NOTE

    (home / "my-explore-world").mkdir()
    beside = check_student_world(kit)
    assert beside.status == OK
    assert "never delete" in beside.detail

    (kit / "my-explore-world").mkdir()
    assert check_student_world(kit).status == HELP


# --- Computer-only mode -------------------------------------------------------------


def reachable_network() -> tuple[bool, str]:
    return True, "the internet is reachable"


def unreachable_network() -> tuple[bool, str]:
    return False, "could not reach the internet (OSError)"


def test_computer_only_mode_never_says_ready(tmp_path):
    results = run_checks(
        workspace=tmp_path, computer_only=True, network_probe=reachable_network, **COMPUTER
    )

    assert overall_result(results, computer_only=True) == COMPUTER_ONLY_BANNER
    report = format_report(results, computer_only=True)
    assert "READY" not in report
    assert "Course folder" not in report


@pytest.mark.parametrize(
    ("override", "expected_check"),
    [
        ({"version": (3, 10, 14)}, "Python version"),
        ({"total_memory_bytes": 4 * 1000**3}, "Memory (RAM)"),
        ({"free_disk_bytes": 2 * 1000**3}, "Free storage"),
        ({"network_probe": unreachable_network}, "Internet connection"),
        ({"system": "Windows", "wsl": False}, "Operating system"),
    ],
)
def test_computer_only_mode_reports_each_unmet_requirement(tmp_path, override, expected_check):
    settings = {**COMPUTER, "network_probe": reachable_network, **override}
    results = run_checks(workspace=tmp_path, computer_only=True, **settings)

    assert overall_result(results, computer_only=True) == HELP_BANNER
    assert expected_check in [result.name for result in results if result.status == HELP]


def test_ubuntu_needs_python3_venv_and_unzip(tmp_path):
    ubuntu = {
        **COMPUTER,
        "system": "Linux",
        "wsl": True,
        "wsl_version": 2,
        "environ": {"DISPLAY": ":0"},
    }

    def venv_broken() -> tuple[bool, str]:
        return False, "python3 -m venv does not work yet (python3-venv is missing)"

    results = run_checks(
        workspace=tmp_path,
        computer_only=True,
        network_probe=reachable_network,
        venv_probe=venv_broken,
        unzip_available=False,
        **ubuntu,
    )
    assert "python3-venv" in named(results, "Python can make a .venv").advice
    assert named(results, "unzip command").status == HELP


# --- Hardware and platform (unchanged floor) ----------------------------------------


def test_minimum_memory_and_storage_match_the_documented_hardware_floor():
    assert MINIMUM_MEMORY_BYTES == 8 * 1000**3
    assert MINIMUM_FREE_DISK_BYTES == 5 * 1000**3
    assert check_memory(MINIMUM_MEMORY_BYTES).status == OK
    assert check_memory(MINIMUM_MEMORY_BYTES - 1).status == HELP
    assert check_memory(None).status == NOTE
    assert check_disk_space(MINIMUM_FREE_DISK_BYTES).status == OK
    assert check_disk_space(MINIMUM_FREE_DISK_BYTES - 1).status == HELP


def test_supported_platforms_are_macos_linux_and_wsl_2():
    assert check_operating_system("Darwin", False).status == OK
    assert check_operating_system("Linux", True, 2).status == OK
    assert check_operating_system("Linux", False).status == OK
    assert check_operating_system("Linux", True, 1).status == HELP
    assert "WSL 2" in check_operating_system("Windows", False).advice
    assert "Chromebook" in check_operating_system("iOS", False).advice


def test_wsl_requires_wslg():
    assert check_display("Linux", True, {}).status == HELP
    assert check_display("Linux", True, {"DISPLAY": ":0"}).status == OK
    assert check_display("Linux", True, {"WAYLAND_DISPLAY": "wayland-0"}).status == OK
    assert check_display("Darwin", False, {}).status == OK


# --- Report and command --------------------------------------------------------------


def test_report_never_prints_the_home_directory_or_asks_for_personal_data(tmp_path):
    real_home = Path.home()
    assert shorten_home(real_home) == "~"
    assert shorten_home(real_home / "course") == str(Path("~") / "course")

    kit = make_kit(tmp_path / "explore-studio-course")
    report = format_report(
        run_checks(
            workspace=kit,
            home=real_home,
            runtime=runtime_for(real_home / "explore-studio-course"),
            trail_launcher=trail_opened,
            **COMPUTER,
        )
    )
    assert str(real_home) not in report
    assert "sends nothing anywhere" in report
    assert "never asks for a password, an account, or any personal detail" in report


def test_command_exits_one_with_one_banner_outside_a_course_kit(tmp_path):
    stream = io.StringIO()
    exit_code = main(["--workspace", str(tmp_path)], stream=stream)
    printed = stream.getvalue()

    assert exit_code == 1
    assert "WRONG FOLDER" in printed
    assert printed.count(HELP_BANNER) == 1
    assert READY_BANNER not in printed


def test_readiness_check_runs_on_the_standard_library_alone():
    source = (PROJECT_ROOT / "scripts" / "check_computer_readiness.py").read_text(encoding="utf-8")

    assert "import pygame" in source, "the Trail probe imports pygame lazily"
    top_level = [
        line
        for line in source.splitlines()
        if re.match(r"(import|from) ", line) and "__future__" not in line
    ]
    third_party = {"pygame", "yaml", "cryptography", "jwt", "starlette", "httpx", "explore"}
    for line in top_level:
        module = line.split()[1].split(".")[0]
        assert module not in third_party, f"{module} must not be imported before install"
