"""Student- and parent-facing computer readiness check for Explore Studio.

Run this before the first session:

```console
python3 check-my-computer.py
```

The check uses only the Python standard library so it can run before any course
dependency is installed. It reads local hardware and environment facts, prints
them on this computer's own screen, and ends with one of two results:

```text
READY FOR EXPLORE STUDIO
SETUP HELP NEEDED
```

Privacy boundary: this check never asks for, reads, or stores a password,
token, account name, email address, or any other personal detail, and it never
uploads anything. The one network step opens a connection to confirm the
internet works and sends no data. Home-directory paths are shortened to ``~``
before printing so a shared screen or pasted result does not expose a name.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MINIMUM_PYTHON = (3, 11)
MINIMUM_MEMORY_BYTES = 8 * 1000**3
MINIMUM_FREE_DISK_BYTES = 5 * 1000**3
NETWORK_PROBE_HOST = "github.com"
NETWORK_PROBE_PORT = 443
NETWORK_TIMEOUT_SECONDS = 8.0
READY_BANNER = "READY FOR EXPLORE STUDIO"
HELP_BANNER = "SETUP HELP NEEDED"

OK = "ok"
HELP = "help"
NOTE = "note"


@dataclass(frozen=True)
class CheckResult:
    """One readiness question and its plain-language answer.

    Attributes:
        name: Short student-readable label for the thing being checked.
        status: ``ok``, ``help``, or ``note``. Only ``help`` blocks readiness.
        detail: What this computer actually reported.
        advice: What to do next when the status is not ``ok``.
    """

    name: str
    status: str
    detail: str
    advice: str = ""


def shorten_home(path: Path) -> str:
    """Return ``path`` with the home directory replaced by ``~``.

    Keeps a printed or pasted result from exposing an account name.
    """
    text = str(path)
    home = str(Path.home())
    if text == home:
        return "~"
    if text.startswith(home + os.sep):
        return "~" + text[len(home) :]
    return text


def is_wsl() -> bool:
    """Return True when this Linux environment is Windows Subsystem for Linux."""
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def detect_total_memory_bytes() -> int | None:
    """Return installed memory in bytes, or None when it cannot be measured."""
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if pages > 0 and page_size > 0:
            return pages * page_size
    except (OSError, ValueError, AttributeError):
        pass
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    if sys.platform == "darwin":
        try:
            completed = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if completed.returncode == 0:
                return int(completed.stdout.strip())
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    return None


def gigabytes(value: int) -> str:
    """Format a byte count as a short, student-readable GB string."""
    return f"{value / 1000**3:.1f} GB"


def check_operating_system(system: str, wsl: bool) -> CheckResult:
    """Check that this is a supported primary coding computer."""
    if system == "Darwin":
        return CheckResult("Operating system", OK, "macOS")
    if system == "Linux" and wsl:
        return CheckResult("Operating system", OK, "Windows with WSL 2 Ubuntu")
    if system == "Linux":
        return CheckResult("Operating system", OK, "Linux")
    if system == "Windows":
        return CheckResult(
            "Operating system",
            HELP,
            "Windows without WSL",
            "Explore Studio runs on Windows through WSL 2 with Ubuntu and WSLg. "
            "Ask an adult to install WSL, then run this check again inside the "
            "Ubuntu window.",
        )
    return CheckResult(
        "Operating system",
        HELP,
        f"{system or 'unknown'} is not a supported course computer",
        "Use a Mac, or Windows with WSL 2 Ubuntu. A phone, tablet, or "
        "Chromebook cannot run this course.",
    )


def check_python(version: tuple[int, ...]) -> CheckResult:
    """Check that the Python running this file is new enough."""
    found = ".".join(str(part) for part in version[:3])
    if version[:2] >= MINIMUM_PYTHON:
        return CheckResult("Python version", OK, f"Python {found}")
    return CheckResult(
        "Python version",
        HELP,
        f"Python {found}",
        "Explore Studio needs Python 3.11 or newer. Ask an adult to install a "
        "newer Python from python.org (macOS) or with `sudo apt install "
        "python3` (Ubuntu in WSL).",
    )


def check_memory(total_bytes: int | None) -> CheckResult:
    """Check installed memory against the 8 GB course minimum."""
    if total_bytes is None:
        return CheckResult(
            "Memory (RAM)",
            NOTE,
            "could not be measured on this computer",
            "Check the computer's About or System Information screen for at "
            "least 8 GB of memory.",
        )
    if total_bytes >= MINIMUM_MEMORY_BYTES:
        return CheckResult("Memory (RAM)", OK, gigabytes(total_bytes))
    return CheckResult(
        "Memory (RAM)",
        HELP,
        f"{gigabytes(total_bytes)} installed, 8 GB needed",
        "This computer has less memory than the course needs. Ask your teacher "
        "which computer to use instead.",
    )


def check_disk_space(free_bytes: int) -> CheckResult:
    """Check free storage against the 5 GB course minimum."""
    if free_bytes >= MINIMUM_FREE_DISK_BYTES:
        return CheckResult("Free storage", OK, f"{gigabytes(free_bytes)} free")
    return CheckResult(
        "Free storage",
        HELP,
        f"{gigabytes(free_bytes)} free, 5 GB needed",
        "Empty the Trash and remove large downloads or videos, then run this " "check again.",
    )


def check_workspace_location(workspace: Path, wsl: bool) -> CheckResult:
    """Check that the course folder is somewhere the course can run from."""
    shown = shorten_home(workspace)
    if wsl and str(workspace).startswith("/mnt/"):
        return CheckResult(
            "Course folder location",
            HELP,
            f"{shown} is on the Windows drive",
            "In WSL, unzip the course inside the Ubuntu home folder, for "
            "example /home/student/explore-studio-course, not /mnt/c.",
        )
    if "downloads" in {part.lower() for part in workspace.parts}:
        return CheckResult(
            "Course folder location",
            NOTE,
            f"{shown} is inside Downloads",
            "Move the unzipped course folder to your home folder or Desktop so "
            "it is easy to find every session.",
        )
    return CheckResult("Course folder location", OK, shown)


def check_display(system: str, wsl: bool, environ: dict[str, str]) -> CheckResult:
    """Check that a window can appear on screen (WSLg on Windows)."""
    if system == "Darwin":
        return CheckResult("Screen for the Trail window", OK, "macOS desktop")
    if wsl:
        if environ.get("DISPLAY") or environ.get("WAYLAND_DISPLAY"):
            return CheckResult("Screen for the Trail window", OK, "WSLg is available")
        return CheckResult(
            "Screen for the Trail window",
            HELP,
            "WSLg was not found in this Ubuntu window",
            "Ask an adult to update WSL (`wsl --update` in Windows PowerShell) "
            "and restart it, so Linux apps can open windows.",
        )
    if environ.get("DISPLAY") or environ.get("WAYLAND_DISPLAY"):
        return CheckResult("Screen for the Trail window", OK, "desktop is available")
    return CheckResult(
        "Screen for the Trail window",
        HELP,
        "no desktop display was found",
        "Run this check from the computer's normal desktop, not a text-only " "remote session.",
    )


def check_keyboard() -> CheckResult:
    """Record the physical keyboard requirement, which software cannot detect."""
    return CheckResult(
        "Physical keyboard",
        NOTE,
        "please confirm by hand",
        "Type a few letters and press the W, A, S, D, and E keys. An on-screen "
        "touch keyboard is not enough for this course.",
    )


def check_internet(probe) -> CheckResult:
    """Check that the internet is reachable for the one-time setup download."""
    reachable, detail = probe()
    if reachable:
        return CheckResult("Internet connection", OK, detail)
    return CheckResult(
        "Internet connection",
        HELP,
        detail,
        "Connect to Wi-Fi or a network cable and run this check again. The "
        "course needs the internet once, to install the lesson tools.",
    )


def probe_network() -> tuple[bool, str]:
    """Open and immediately close a connection to confirm internet access.

    No data is sent and no account information is used.
    """
    try:
        with socket.create_connection(
            (NETWORK_PROBE_HOST, NETWORK_PROBE_PORT), timeout=NETWORK_TIMEOUT_SECONDS
        ):
            return True, "the internet is reachable"
    except OSError as error:
        return False, f"could not reach the internet ({error.__class__.__name__})"


def check_trail_launch(launcher) -> CheckResult:
    """Open and close one minimal Trail window when that is possible yet."""
    outcome, detail = launcher()
    if outcome == "skipped":
        return CheckResult(
            "Trail window opens and closes",
            NOTE,
            detail,
            "Run this check again after the first-session install to test a " "real Trail window.",
        )
    if outcome == "ok":
        return CheckResult("Trail window opens and closes", OK, detail)
    return CheckResult(
        "Trail window opens and closes",
        HELP,
        detail,
        "The graphics library is installed but could not open a window. Show "
        "this result to your teacher.",
    )


def launch_minimal_trail() -> tuple[str, str]:
    """Open and close a tiny graphics window using the installed course engine.

    Returns ``("skipped", ...)`` before the course tools are installed, so the
    same command is useful on the very first run.
    """
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ImportError:
        return "skipped", "course tools are not installed yet"
    try:
        pygame.display.init()
        surface = pygame.display.set_mode((160, 120))
        del surface
        pygame.display.quit()
    except Exception as error:  # noqa: BLE001 - any driver failure is one answer
        return "failed", f"a window could not open ({error.__class__.__name__})"
    finally:
        with contextlib.suppress(Exception):
            pygame.quit()
    return "ok", "a test window opened and closed"


def run_checks(
    *,
    workspace: Path,
    system: str | None = None,
    wsl: bool | None = None,
    version: tuple[int, ...] | None = None,
    environ: dict[str, str] | None = None,
    total_memory_bytes: int | None = None,
    free_disk_bytes: int | None = None,
    network_probe=None,
    trail_launcher=None,
) -> list[CheckResult]:
    """Run every readiness check and return the results in reading order."""
    system = platform.system() if system is None else system
    wsl = is_wsl() if wsl is None else wsl
    version = tuple(sys.version_info[:3]) if version is None else version
    environ = dict(os.environ) if environ is None else environ
    if total_memory_bytes is None:
        total_memory_bytes = detect_total_memory_bytes()
    if free_disk_bytes is None:
        free_disk_bytes = shutil.disk_usage(workspace).free
    network_probe = probe_network if network_probe is None else network_probe
    trail_launcher = launch_minimal_trail if trail_launcher is None else trail_launcher

    return [
        check_operating_system(system, wsl),
        check_python(version),
        check_memory(total_memory_bytes),
        check_disk_space(free_disk_bytes),
        check_workspace_location(workspace, wsl),
        check_display(system, wsl, environ),
        check_keyboard(),
        check_internet(network_probe),
        check_trail_launch(trail_launcher),
    ]


def overall_result(results: list[CheckResult]) -> str:
    """Return the single banner line students and parents read."""
    if any(result.status == HELP for result in results):
        return HELP_BANNER
    return READY_BANNER


def format_report(results: list[CheckResult]) -> str:
    """Build the full printed report, ending with the one-line result."""
    lines = [
        "Explore Studio — computer check",
        "",
        "This check looks only at this computer and sends nothing anywhere.",
        "It never asks for a password, an account, or any personal detail.",
        "",
    ]
    marker = {OK: "[ ok ]", HELP: "[help]", NOTE: "[note]"}
    for result in results:
        lines.append(f"{marker[result.status]} {result.name}: {result.detail}")
        if result.advice:
            lines.append(f"        -> {result.advice}")
    banner = overall_result(results)
    lines.extend(["", banner, ""])
    if banner == HELP_BANNER:
        lines.append(
            "Show the lines marked [help] to a teacher or an adult at home. "
            "Nothing is broken; this computer just needs one more setup step."
        )
    else:
        lines.append(
            "This computer is ready. Open the course folder and follow "
            "START-HERE.md to begin Session 1."
        )
    return "\n".join(lines) + "\n"


def main(argv=None, stream=None) -> int:
    """Run the student-facing computer check and print its result."""
    parser = argparse.ArgumentParser(
        description="Check whether this computer is ready for Explore Studio."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="course folder to check (defaults to the current folder)",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="skip the internet check when testing offline on purpose",
    )
    args = parser.parse_args(argv)

    network_probe = None
    if args.skip_network:

        def network_probe() -> tuple[bool, str]:
            return True, "skipped at your request"

    results = run_checks(
        workspace=args.workspace.resolve(),
        network_probe=network_probe,
    )
    print(format_report(results), end="", file=stream or sys.stdout)
    return 0 if overall_result(results) == READY_BANNER else 1


if __name__ == "__main__":
    raise SystemExit(main())
