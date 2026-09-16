from __future__ import annotations

import io
from pathlib import Path

import pytest

from scripts.check_computer_readiness import (
    HELP,
    HELP_BANNER,
    MINIMUM_FREE_DISK_BYTES,
    MINIMUM_MEMORY_BYTES,
    NOTE,
    OK,
    READY_BANNER,
    check_disk_space,
    check_display,
    check_memory,
    check_operating_system,
    check_python,
    check_workspace_location,
    format_report,
    main,
    overall_result,
    run_checks,
    shorten_home,
)

PROJECT_ROOT = Path(__file__).parents[1]

READY_ENVIRONMENT = {
    "system": "Darwin",
    "wsl": False,
    "version": (3, 11, 9),
    "environ": {},
    "total_memory_bytes": MINIMUM_MEMORY_BYTES,
    "free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
}


def reachable_network() -> tuple[bool, str]:
    return True, "the internet is reachable"


def unreachable_network() -> tuple[bool, str]:
    return False, "could not reach the internet (OSError)"


def trail_opened() -> tuple[str, str]:
    return "ok", "a test window opened and closed"


def trail_not_installed() -> tuple[str, str]:
    return "skipped", "course tools are not installed yet"


def trail_failed() -> tuple[str, str]:
    return "failed", "a window could not open (error)"


def results_for(workspace: Path, **overrides):
    settings = {**READY_ENVIRONMENT, **overrides}
    settings.setdefault("network_probe", reachable_network)
    settings.setdefault("trail_launcher", trail_opened)
    return run_checks(workspace=workspace, **settings)


def test_a_supported_computer_reports_ready(tmp_path):
    results = results_for(tmp_path)

    assert overall_result(results) == READY_BANNER
    assert all(result.status in {OK, NOTE} for result in results)


def test_a_ready_computer_before_install_is_still_ready(tmp_path):
    results = results_for(tmp_path, trail_launcher=trail_not_installed)

    assert overall_result(results) == READY_BANNER
    trail = next(result for result in results if result.name == "Trail window opens and closes")
    assert trail.status == NOTE
    assert "not installed yet" in trail.detail


@pytest.mark.parametrize(
    ("override", "expected_check"),
    [
        ({"version": (3, 10, 14)}, "Python version"),
        ({"total_memory_bytes": 4 * 1000**3}, "Memory (RAM)"),
        ({"free_disk_bytes": 2 * 1000**3}, "Free storage"),
        ({"network_probe": unreachable_network}, "Internet connection"),
        ({"trail_launcher": trail_failed}, "Trail window opens and closes"),
        ({"system": "Windows", "wsl": False}, "Operating system"),
    ],
)
def test_each_unmet_requirement_reports_setup_help_needed(tmp_path, override, expected_check):
    results = results_for(tmp_path, **override)

    assert overall_result(results) == HELP_BANNER
    failed = [result.name for result in results if result.status == HELP]
    assert expected_check in failed


def test_python_311_is_the_minimum_supported_version():
    assert check_python((3, 11, 0)).status == OK
    assert check_python((3, 12, 5)).status == OK
    assert check_python((3, 10, 14)).status == HELP


def test_minimum_memory_and_storage_match_the_documented_hardware_floor():
    assert MINIMUM_MEMORY_BYTES == 8 * 1000**3
    assert MINIMUM_FREE_DISK_BYTES == 5 * 1000**3
    assert check_memory(MINIMUM_MEMORY_BYTES).status == OK
    assert check_memory(MINIMUM_MEMORY_BYTES - 1).status == HELP
    assert check_disk_space(MINIMUM_FREE_DISK_BYTES).status == OK
    assert check_disk_space(MINIMUM_FREE_DISK_BYTES - 1).status == HELP


def test_unmeasurable_memory_is_a_note_and_never_blocks_readiness(tmp_path):
    memory = check_memory(None)
    assert memory.status == NOTE

    results = results_for(tmp_path, total_memory_bytes=None)
    assert overall_result(results) == READY_BANNER


def test_supported_platforms_are_macos_and_wsl_ubuntu():
    assert check_operating_system("Darwin", False).status == OK
    assert check_operating_system("Linux", True).status == OK
    assert check_operating_system("Linux", False).status == OK

    windows = check_operating_system("Windows", False)
    assert windows.status == HELP
    assert "WSL 2" in windows.advice

    other = check_operating_system("iOS", False)
    assert other.status == HELP
    assert "Chromebook" in other.advice


def test_wsl_requires_wslg_and_a_linux_home_course_folder():
    assert check_display("Linux", True, {}).status == HELP
    assert check_display("Linux", True, {"DISPLAY": ":0"}).status == OK
    assert check_display("Linux", True, {"WAYLAND_DISPLAY": "wayland-0"}).status == OK
    assert check_display("Darwin", False, {}).status == OK

    on_windows_drive = check_workspace_location(Path("/mnt/c/Users/student/course"), True)
    assert on_windows_drive.status == HELP
    assert "/mnt/c" in on_windows_drive.advice

    in_linux_home = check_workspace_location(Path("/home/student/explore-studio-course"), True)
    assert in_linux_home.status == OK


def test_downloads_is_a_note_rather_than_a_blocking_failure():
    result = check_workspace_location(Path("/Users/student/Downloads/course"), False)

    assert result.status == NOTE
    assert "Downloads" in result.detail


def test_report_never_prints_the_home_directory_or_asks_for_personal_data(tmp_path):
    home = Path.home()
    assert shorten_home(home) == "~"
    assert shorten_home(home / "course") == str(Path("~") / "course")

    report = format_report(results_for(home / "course"))
    assert str(home) not in report
    assert "sends nothing anywhere" in report
    assert "never asks for a password, an account, or any personal detail" in report


def test_report_ends_with_exactly_one_result_banner(tmp_path):
    ready = format_report(results_for(tmp_path))
    assert READY_BANNER in ready
    assert HELP_BANNER not in ready

    blocked = format_report(results_for(tmp_path, version=(3, 9, 0)))
    assert HELP_BANNER in blocked
    assert READY_BANNER not in blocked
    assert "[help] Python version" in blocked


def test_command_exits_zero_when_ready_and_one_when_help_is_needed(tmp_path):
    stream = io.StringIO()
    exit_code = main(["--workspace", str(tmp_path), "--skip-network"], stream=stream)
    printed = stream.getvalue()

    assert exit_code in {0, 1}
    assert (
        printed.rstrip().endswith("START-HERE.md to begin Session 1.")
        or "SETUP HELP NEEDED" in printed
    )
    assert (READY_BANNER in printed) != (HELP_BANNER in printed)
    assert (exit_code == 0) == (READY_BANNER in printed)


def test_readiness_check_runs_on_the_standard_library_alone():
    source = (PROJECT_ROOT / "scripts" / "check_computer_readiness.py").read_text(encoding="utf-8")

    assert "import pygame" in source, "the Trail probe imports pygame lazily"
    top_level = [
        line
        for line in source.splitlines()
        if line.startswith(("import ", "from ")) and "__future__" not in line
    ]
    third_party = {"pygame", "yaml", "cryptography", "jwt", "starlette", "httpx"}
    for line in top_level:
        module = line.split()[1].split(".")[0]
        assert module not in third_party, f"{module} must not be imported before install"
