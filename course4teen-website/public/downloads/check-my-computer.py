"""Student-, parent-, and teacher-facing readiness check for Explore Studio.

Run it from the Course Kit with the course ``.venv`` active:

```console
cd ~/explore-studio-course
source .venv/bin/activate
python3 check-my-computer.py
```

The check uses only the Python standard library, reads only local facts, never
touches the network in this mode, and ends with a short summary a teacher can
read at a glance, then exactly one result:

```text
Summary
  Python: 3.12.3
  Course folder: OK
  Virtual environment: .venv
  Course tools: 2e5d5ef (current)
  Trail dependency: OK

READY FOR EXPLORE STUDIO
```

or ``SETUP HELP NEEDED``. READY is printed only when every blocking item passes:
the right folder, the Course Kit's own ``.venv`` active, a supported Python, the
course tools installed at exactly the commit this Course Kit pins in
``requirements-student.txt``, and the Trail's graphics library. An out-of-date
install is the most common reason an old Trail looks like a new bug, so it is
always blocking.

``python3 check-my-computer.py --computer-only`` checks just the computer, for a
family testing a machine before the course is installed. It never prints READY;
it ends with ``COMPUTER CHECK PASSED`` or ``SETUP HELP NEEDED``.

Privacy boundary: this check never asks for, reads, or stores a password,
token, account name, email address, or any other personal detail, and it never
uploads anything. Only ``--computer-only`` opens one network connection, to
confirm the internet works for the one-time install, and it sends no data.
Home-directory paths are shortened to ``~`` before printing so a shared screen
or pasted result does not expose a name.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

MINIMUM_PYTHON = (3, 11)
MINIMUM_MEMORY_BYTES = 8 * 1000**3
MINIMUM_FREE_DISK_BYTES = 5 * 1000**3
NETWORK_PROBE_HOST = "github.com"
NETWORK_PROBE_PORT = 443
NETWORK_TIMEOUT_SECONDS = 8.0
VENV_PROBE_TIMEOUT_SECONDS = 180.0
READY_BANNER = "READY FOR EXPLORE STUDIO"
HELP_BANNER = "SETUP HELP NEEDED"
COMPUTER_ONLY_BANNER = "COMPUTER CHECK PASSED"

#: The replaceable Course Kit and the student's own folder beside it. Every
#: setup page uses these exact names.
COURSE_KIT_NAME = "explore-studio-course"
STUDENT_WORLD_NAME = "my-explore-world"
COURSE_KIT_MARKERS = ("START-HERE.md", "requirements-student.txt", "course-materials.json")
#: A teacher-managed Git course folder also ships this pin and may use any name.
GIT_COURSE_PIN = "requirements-course.txt"
STUDENT_PIN = "requirements-student.txt"
VENV_NAME = ".venv"
PLATFORM_DISTRIBUTION = "explore-studio"
TRAIL_DEPENDENCY = "pygame"
#: The pin form used by ``requirements-student.txt`` (an HTTPS archive of one
#: commit) and ``requirements-course.txt`` (``git+https://...@<commit>``).
PIN_PATTERN = re.compile(r"^explore-studio\s*@\s*\S*?\b([0-9a-f]{40})\b", re.MULTILINE)
COMMIT_PATTERN = re.compile(r"\b[0-9a-f]{40}\b")
SETUP_GUIDE = "docs/windows-wsl-setup.md"

GO_TO_KIT = "cd ~/explore-studio-course"
ACTIVATE = "source .venv/bin/activate"
INSTALL = "python -m pip install -r requirements-student.txt"
#: Plain ``pip install -r`` keeps an older install of the same package version
#: ("Requirement already satisfied") even when the pinned commit changed, so
#: replacing stale course tools needs ``--force-reinstall``.
FORCE_REINSTALL = "python -m pip install --force-reinstall -r requirements-student.txt"
MAKE_VENV = f"python3 -m venv .venv, then `{ACTIVATE}`, then `{INSTALL}`"

OK = "ok"
HELP = "help"
NOTE = "note"

PYTHON_CHECK = "Python version"
FOLDER_CHECK = "Course folder"
VENV_CHECK = "Virtual environment"
TOOLS_CHECK = "Course tools"
TRAIL_DEPENDENCY_CHECK = "Trail dependency"
#: READY needs every one of these to be ``ok``, not merely free of ``help``.
BLOCKING_CHECKS = (PYTHON_CHECK, FOLDER_CHECK, VENV_CHECK, TOOLS_CHECK, TRAIL_DEPENDENCY_CHECK)


@dataclass(frozen=True)
class CheckResult:
    """One readiness question and its plain-language answer.

    Attributes:
        name: Short student-readable label for the thing being checked.
        status: ``ok``, ``help``, or ``note``. ``help`` always blocks readiness.
        detail: What this computer actually reported.
        advice: What to do next when the status is not ``ok``.
        summary: The short value shown in the final summary, for blocking items.
    """

    name: str
    status: str
    detail: str
    advice: str = ""
    summary: str = ""


@dataclass(frozen=True)
class RuntimeFacts:
    """What the Python running this check has installed, read offline.

    Attributes:
        prefix: ``sys.prefix`` of the running Python (the active ``.venv``).
        in_venv: True when that Python is a virtual environment.
        platform_installed: True when the course tools distribution is present.
        installed_commit: The commit pip recorded for it (PEP 610), if any.
        launcher_prefix: The environment ``explore-package`` was installed for,
            read from its script; differs from ``prefix`` when a ``.venv`` was
            moved or copied after the install.
        trail_dependency_installed: True when ``pygame`` can be imported.
    """

    prefix: Path
    in_venv: bool
    platform_installed: bool
    installed_commit: str | None
    launcher_prefix: Path | None
    trail_dependency_installed: bool


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


def detect_wsl_version() -> int | None:
    """Return 1 or 2 for WSL, or None when this is not WSL or it is unclear."""
    try:
        kernel = Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return None
    if "microsoft" not in kernel:
        return None
    return 2 if ("wsl2" in kernel or "microsoft-standard" in kernel) else 1


def is_course_kit(path: Path) -> bool:
    """Return True when ``path`` is the root of a Course Kit (or Git course folder)."""
    return all((path / marker).is_file() for marker in COURSE_KIT_MARKERS)


def is_zip_course_kit(path: Path) -> bool:
    """Return True for the student ZIP Course Kit, which has one canonical home."""
    return is_course_kit(path) and not (path / GIT_COURSE_PIN).exists()


def _same_place(left: Path, right: Path) -> bool:
    return os.path.realpath(left) == os.path.realpath(right)


def read_expected_pin(workspace: Path) -> str | None:
    """Return the course tools commit this Course Kit pins, or None.

    Read from ``requirements-student.txt`` (the ZIP install), falling back to
    ``requirements-course.txt`` for a Git-managed course folder. Never
    hard-coded, so the check stays correct across pin bumps.
    """
    for pin_name in (STUDENT_PIN, GIT_COURSE_PIN):
        try:
            match = PIN_PATTERN.search((workspace / pin_name).read_text(encoding="utf-8"))
        except OSError:
            continue
        if match:
            return match.group(1)
    return None


def read_course_kit_version(workspace: Path) -> str | None:
    """Return the commit the Course Kit's materials were built from, or None."""
    try:
        record = json.loads((workspace / "course-materials.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    commit = record.get("course_materials_source_commit") if isinstance(record, dict) else None
    return commit if isinstance(commit, str) and COMMIT_PATTERN.fullmatch(commit) else None


def commit_from_direct_url(text: str | None) -> str | None:
    """Return the commit in a PEP 610 ``direct_url.json`` record, if any.

    Handles both course install forms: an HTTPS archive URL that names the
    commit (``.../archive/<commit>.tar.gz``) and a Git install's
    ``vcs_info.commit_id``. An editable or local install has no commit.
    """
    if not text:
        return None
    try:
        record = json.loads(text)
    except ValueError:
        return None
    if not isinstance(record, dict):
        return None
    vcs = record.get("vcs_info")
    commit = vcs.get("commit_id") if isinstance(vcs, dict) else None
    if isinstance(commit, str) and COMMIT_PATTERN.fullmatch(commit):
        return commit
    url = record.get("url")
    if isinstance(url, str) and "archive_info" in record:
        match = COMMIT_PATTERN.search(url)
        if match:
            return match.group(0)
    return None


def _script_prefix(script: Path) -> Path | None:
    """Return the environment a console script's ``#!`` line points into."""
    try:
        with script.open("rb") as handle:
            first = handle.readline().decode("utf-8", "replace").strip()
    except OSError:
        return None
    if not first.startswith("#!"):
        return None
    command = first[2:].strip().split()
    return Path(command[0]).parent.parent if command else None


def detect_runtime() -> RuntimeFacts:
    """Read the running Python's course install from local metadata only."""
    prefix = Path(sys.prefix)
    try:
        distribution = importlib.metadata.distribution(PLATFORM_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError:
        distribution = None
    return RuntimeFacts(
        prefix=prefix,
        in_venv=sys.prefix != sys.base_prefix,
        platform_installed=distribution is not None,
        installed_commit=(
            commit_from_direct_url(distribution.read_text("direct_url.json"))
            if distribution is not None
            else None
        ),
        launcher_prefix=_script_prefix(prefix / "bin" / "explore-package"),
        trail_dependency_installed=importlib.util.find_spec(TRAIL_DEPENDENCY) is not None,
    )


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


def check_operating_system(system: str, wsl: bool, wsl_version: int | None = None) -> CheckResult:
    """Check that this is a supported primary coding computer."""
    if system == "Darwin":
        return CheckResult("Operating system", OK, "macOS")
    if system == "Linux" and wsl and wsl_version == 1:
        return CheckResult(
            "Operating system",
            HELP,
            "Windows with WSL 1",
            "Explore Studio needs WSL 2. In Windows PowerShell, run `wsl -l -v` "
            "to see the Ubuntu name, then `wsl --set-version <that name> 2`.",
        )
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
            f"Ubuntu window. See {SETUP_GUIDE}.",
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
        return CheckResult(PYTHON_CHECK, OK, f"Python {found}", summary=found)
    return CheckResult(
        PYTHON_CHECK,
        HELP,
        f"Python {found} is too old; Explore Studio needs 3.11 or newer",
        "Stop here: do not continue with this Python. On Windows, install "
        f"Ubuntu 24.04 in WSL (see {SETUP_GUIDE}); installing `python3` on an "
        "older Ubuntu still gives Python 3.10. On a Mac, install Python from "
        "python.org. Then make a fresh .venv.",
        summary=f"{found} (TOO OLD, needs 3.11+)",
    )


def check_venv_support(probe) -> CheckResult:
    """Check that Ubuntu's ``python3-venv`` package can make a course ``.venv``."""
    works, detail = probe()
    if works:
        return CheckResult("Python can make a .venv", OK, detail)
    return CheckResult(
        "Python can make a .venv",
        HELP,
        detail,
        "Install the missing Ubuntu packages: "
        "`sudo apt update && sudo apt install -y python3 python3-venv python3-pip unzip`",
    )


def probe_venv_support() -> tuple[bool, str]:
    """Make and delete one throwaway virtual environment with pip inside it.

    On Ubuntu, ``python3 -m venv`` fails until the ``python3-venv`` package is
    installed. Trying it in a temporary folder is the only reliable test.
    """
    with tempfile.TemporaryDirectory(prefix="explore-venv-check-") as scratch:
        target = Path(scratch) / "probe"
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "venv", str(target)],
                capture_output=True,
                text=True,
                check=False,
                timeout=VENV_PROBE_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return False, f"python3 -m venv could not run ({error.__class__.__name__})"
        if completed.returncode == 0 and (target / "bin" / "pip").exists():
            return True, "python3 -m venv works"
    return False, "python3 -m venv does not work yet (python3-venv is missing)"


def check_unzip(available: bool) -> CheckResult:
    """Check that ``unzip`` is installed for unpacking each new Course Kit."""
    if available:
        return CheckResult("unzip command", OK, "installed")
    return CheckResult(
        "unzip command",
        HELP,
        "not installed",
        "You need it to unpack each new Course Kit: `sudo apt install -y unzip`",
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
        "Empty the Trash and remove large downloads or videos, then run this check again.",
    )


def check_course_folder(workspace: Path, wsl: bool, home: Path) -> CheckResult:
    """Check this is run from the Course Kit root, and the kit is in its one place.

    The ZIP Course Kit belongs at ``~/explore-studio-course`` with the
    student's ``my-explore-world`` beside it, and every lesson command runs
    from the Course Kit root.
    """
    shown = shorten_home(workspace)
    canonical = f"~/{COURSE_KIT_NAME}"
    rerun = f"Run `{GO_TO_KIT}`, then `python3 check-my-computer.py` again."
    wrong_place = "COURSE FOLDER IN WRONG PLACE"
    if not is_course_kit(workspace):
        if workspace.name == STUDENT_WORLD_NAME:
            detail = f"WRONG FOLDER: {shown} is your world folder, not the Course Kit"
        else:
            detail = f"WRONG FOLDER: {shown} is not the Course Kit"
        return CheckResult(
            FOLDER_CHECK,
            HELP,
            detail,
            f"Lesson commands and this check run from the Course Kit. {rerun}",
            summary="WRONG FOLDER",
        )
    if workspace.parent.name == COURSE_KIT_NAME or is_course_kit(workspace / COURSE_KIT_NAME):
        return CheckResult(
            FOLDER_CHECK,
            HELP,
            f"{wrong_place}: {shown} is one course folder inside another",
            f"Unzip so there is only one {COURSE_KIT_NAME} folder, at {canonical}. "
            f"See {SETUP_GUIDE}.",
            summary=wrong_place,
        )
    if wsl and str(workspace).startswith("/mnt/"):
        return CheckResult(
            FOLDER_CHECK,
            HELP,
            f"{wrong_place}: {shown} is on the Windows drive",
            f"In WSL the course must live in the Ubuntu home folder, at {canonical}, "
            f"never under /mnt/c. See {SETUP_GUIDE}.",
            summary=wrong_place,
        )
    if "downloads" in {part.lower() for part in workspace.parts}:
        return CheckResult(
            FOLDER_CHECK,
            HELP,
            f"{wrong_place}: {shown} is inside Downloads",
            f"Move the course folder to {canonical}. See {SETUP_GUIDE}.",
            summary=wrong_place,
        )
    if is_zip_course_kit(workspace) and not _same_place(workspace, home / COURSE_KIT_NAME):
        return CheckResult(
            FOLDER_CHECK,
            HELP,
            f"{wrong_place}: {shown} is not {canonical}",
            f"Move it to {canonical}, and move {STUDENT_WORLD_NAME} (if you have "
            f"one) to ~/{STUDENT_WORLD_NAME}. See {SETUP_GUIDE}.",
            summary=wrong_place,
        )
    return CheckResult(FOLDER_CHECK, OK, shown, summary="OK")


def check_course_kit_version(workspace: Path) -> CheckResult:
    """Report which Course Kit this is, so a stale kit is easy to spot."""
    materials = read_course_kit_version(workspace)
    if materials is None:
        return CheckResult(
            "Course Kit version",
            HELP,
            "course-materials.json is missing or unreadable",
            "This course folder is damaged. Get a fresh Course Kit: see "
            f"'Get a newer Course Kit' in {SETUP_GUIDE}.",
        )
    return CheckResult(
        "Course Kit version",
        OK,
        f"{materials[:7]} (the course website's Prepare page shows the newest)",
    )


def check_student_world(workspace: Path) -> CheckResult:
    """Check that ``my-explore-world`` sits beside the kit, never inside it."""
    inside = workspace / STUDENT_WORLD_NAME
    beside = workspace.parent / STUDENT_WORLD_NAME
    if inside.exists():
        return CheckResult(
            "Your world folder",
            HELP,
            f"{shorten_home(inside)} is inside the Course Kit",
            "A Course Kit update replaces everything in this folder. Move "
            f"{STUDENT_WORLD_NAME} to ~/{STUDENT_WORLD_NAME}, beside the Course Kit.",
        )
    if beside.is_dir():
        return CheckResult(
            "Your world folder",
            OK,
            f"{shorten_home(beside)} (yours to keep: never delete it)",
        )
    return CheckResult(
        "Your world folder",
        NOTE,
        "not made yet",
        "You make it in Session 2 with `python3 make-my-world.py`.",
    )


def _not_checked(name: str, reason: str) -> CheckResult:
    return CheckResult(name, NOTE, f"not checked until {reason}", summary="not checked")


def check_virtual_environment(workspace: Path, runtime: RuntimeFacts) -> CheckResult:
    """Check the running Python is this Course Kit's own, active ``.venv``."""
    venv = workspace / VENV_NAME
    if not runtime.in_venv:
        if venv.is_dir():
            advice = f"Run `{ACTIVATE}`, then `python3 check-my-computer.py` again."
        else:
            advice = f"There is no .venv here yet. Make it: `{MAKE_VENV}`."
        return CheckResult(
            VENV_CHECK,
            HELP,
            "VENV NOT ACTIVE: this is the computer's own Python, not the course .venv",
            advice,
            summary="VENV NOT ACTIVE",
        )
    if not _same_place(runtime.prefix, venv):
        return CheckResult(
            VENV_CHECK,
            HELP,
            f"VENV IN WRONG PLACE: the active environment is {shorten_home(runtime.prefix)}, "
            f"not {shorten_home(venv)}",
            "The course uses only the .venv inside the Course Kit. Run `deactivate`, "
            f"`{GO_TO_KIT}`, then `{MAKE_VENV}` if it is missing, or just "
            f"`{ACTIVATE}`.",
            summary="VENV IN WRONG PLACE",
        )
    if runtime.launcher_prefix is not None and not _same_place(runtime.launcher_prefix, venv):
        return CheckResult(
            VENV_CHECK,
            HELP,
            "VENV IN WRONG PLACE: this .venv was made in another folder, then moved or copied",
            "Make a fresh one: run `deactivate`, `rm -rf .venv`, then " f"`{MAKE_VENV}`.",
            summary="VENV IN WRONG PLACE",
        )
    return CheckResult(VENV_CHECK, OK, shorten_home(venv), summary=VENV_NAME)


def check_course_tools(workspace: Path, runtime: RuntimeFacts, venv_ok: bool) -> CheckResult:
    """Check the active ``.venv`` holds exactly the course tools this kit pins."""
    if not venv_ok:
        return _not_checked(TOOLS_CHECK, "the Course Kit's .venv is active")
    expected = read_expected_pin(workspace)
    if expected is None:
        return CheckResult(
            TOOLS_CHECK,
            HELP,
            f"{STUDENT_PIN} has no course tools pin",
            f"This course folder is damaged. Get a fresh Course Kit: see {SETUP_GUIDE}.",
            summary="COURSE KIT DAMAGED",
        )
    if not runtime.platform_installed:
        return CheckResult(
            TOOLS_CHECK,
            HELP,
            "COURSE TOOLS NOT INSTALLED in this .venv",
            f"Run `{INSTALL}`, then this check again.",
            summary="COURSE TOOLS NOT INSTALLED",
        )
    if runtime.installed_commit is None:
        return CheckResult(
            TOOLS_CHECK,
            HELP,
            "COURSE TOOLS NOT INSTALLED from this Course Kit (no version record)",
            f"Run `{FORCE_REINSTALL}`, then this check again.",
            summary="COURSE TOOLS NOT INSTALLED",
        )
    if runtime.installed_commit != expected:
        return CheckResult(
            TOOLS_CHECK,
            HELP,
            f"COURSE TOOLS OUT OF DATE: installed {runtime.installed_commit[:7]}, "
            f"this Course Kit needs {expected[:7]}",
            f"Run `{FORCE_REINSTALL}`, then this check again. (Running the plain "
            "install again is not enough: it keeps the old version.)",
            summary=(
                f"COURSE TOOLS OUT OF DATE (installed {runtime.installed_commit[:7]}, "
                f"needs {expected[:7]})"
            ),
        )
    return CheckResult(
        TOOLS_CHECK, OK, f"{expected[:7]} (current)", summary=f"{expected[:7]} (current)"
    )


def check_trail_dependency(runtime: RuntimeFacts, venv_ok: bool) -> CheckResult:
    """Check the Trail's graphics library is installed in the course ``.venv``."""
    if not venv_ok:
        return _not_checked(TRAIL_DEPENDENCY_CHECK, "the Course Kit's .venv is active")
    if runtime.trail_dependency_installed:
        return CheckResult(TRAIL_DEPENDENCY_CHECK, OK, "pygame is installed", summary="OK")
    return CheckResult(
        TRAIL_DEPENDENCY_CHECK,
        HELP,
        "COURSE TOOLS NOT INSTALLED: pygame, which draws the Trail, is missing",
        f"Run `{INSTALL}`, then this check again.",
        summary="COURSE TOOLS NOT INSTALLED (pygame missing)",
    )


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
        "Run this check from the computer's normal desktop, not a text-only remote session.",
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
    """Open and close one minimal Trail window."""
    outcome, detail = launcher()
    if outcome == "ok":
        return CheckResult("Trail window opens and closes", OK, detail)
    if outcome == "skipped":
        return CheckResult("Trail window opens and closes", NOTE, detail)
    return CheckResult(
        "Trail window opens and closes",
        HELP,
        detail,
        "The graphics library is installed but could not open a window. Show "
        "this result to your teacher.",
    )


def launch_minimal_trail() -> tuple[str, str]:
    """Open and close a tiny graphics window using the installed course engine."""
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ImportError:
        return "skipped", "not tested: pygame is not installed"
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


def _computer_checks(
    system, wsl, wsl_version, version, environ, total_memory_bytes, free_disk_bytes, home
):
    return [
        check_operating_system(system, wsl, wsl_version),
        check_python(version),
        check_memory(total_memory_bytes),
        check_disk_space(free_disk_bytes),
        check_display(system, wsl, environ),
        check_keyboard(),
    ]


def run_checks(
    *,
    workspace: Path,
    system: str | None = None,
    wsl: bool | None = None,
    version: tuple[int, ...] | None = None,
    environ: dict[str, str] | None = None,
    total_memory_bytes: int | None = None,
    free_disk_bytes: int | None = None,
    trail_launcher=None,
    wsl_version: int | None = None,
    home: Path | None = None,
    runtime: RuntimeFacts | None = None,
    unzip_available: bool | None = None,
    computer_only: bool = False,
    network_probe=None,
    venv_probe=None,
) -> list[CheckResult]:
    """Run every readiness check and return the results in reading order.

    The full check (the default) never touches the network. ``computer_only``
    checks only the machine and adds the one-time-install internet probe.
    """
    system = platform.system() if system is None else system
    wsl = is_wsl() if wsl is None else wsl
    if wsl and wsl_version is None:
        wsl_version = detect_wsl_version()
    version = tuple(sys.version_info[:3]) if version is None else version
    environ = dict(os.environ) if environ is None else environ
    home = Path.home() if home is None else home
    if total_memory_bytes is None:
        total_memory_bytes = detect_total_memory_bytes()
    if free_disk_bytes is None:
        free_disk_bytes = shutil.disk_usage(workspace).free
    if system == "Linux" and unzip_available is None:
        unzip_available = shutil.which("unzip") is not None

    results = [
        check_operating_system(system, wsl, wsl_version),
        check_python(version),
    ]
    if system == "Linux":
        # Ubuntu ships venv support and unzip as separate packages.
        if computer_only:
            results.append(check_venv_support(venv_probe or probe_venv_support))
        results.append(check_unzip(bool(unzip_available)))
    results.extend(
        [
            check_memory(total_memory_bytes),
            check_disk_space(free_disk_bytes),
            check_display(system, wsl, environ),
            check_keyboard(),
        ]
    )
    if computer_only:
        results.append(check_internet(network_probe or probe_network))
        return results

    runtime = detect_runtime() if runtime is None else runtime
    folder = check_course_folder(workspace, wsl, home)
    results.append(folder)
    if is_course_kit(workspace):
        results.extend([check_course_kit_version(workspace), check_student_world(workspace)])
    venv = (
        check_virtual_environment(workspace, runtime)
        if folder.status == OK
        else _not_checked(VENV_CHECK, "you are in the Course Kit folder")
    )
    venv_ok = venv.status == OK
    dependency = check_trail_dependency(runtime, venv_ok)
    results.extend([venv, check_course_tools(workspace, runtime, venv_ok), dependency])
    if dependency.status == OK:
        results.append(check_trail_launch(trail_launcher or launch_minimal_trail))
    return results


def overall_result(results: list[CheckResult], computer_only: bool = False) -> str:
    """Return the single result line students, parents, and teachers read.

    READY needs no ``help`` line *and* every blocking item present and ``ok``,
    so a check that was skipped can never count as passing.
    """
    if any(result.status == HELP for result in results):
        return HELP_BANNER
    if computer_only:
        return COMPUTER_ONLY_BANNER
    passed = {result.name for result in results if result.status == OK}
    if not all(name in passed for name in BLOCKING_CHECKS):
        return HELP_BANNER
    return READY_BANNER


def format_report(results: list[CheckResult], computer_only: bool = False) -> str:
    """Build the full printed report, ending with the summary and one result."""
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
    if not computer_only:
        by_name = {result.name: result for result in results}
        lines.extend(["", "Summary"])
        for name in BLOCKING_CHECKS:
            shown = by_name[name].summary if name in by_name else "not checked"
            lines.append(f"  {name if name != PYTHON_CHECK else 'Python'}: {shown}")
    banner = overall_result(results, computer_only)
    lines.extend(["", banner, ""])
    if banner == HELP_BANNER:
        lines.append(
            "Show the lines marked [help] to a teacher or an adult at home and "
            f"follow their arrows. Setup steps are in {SETUP_GUIDE}."
        )
    elif banner == COMPUTER_ONLY_BANNER:
        lines.append(
            "This computer can run the course. Next: set up the Course Kit "
            "(START-HERE.md), then run `python3 check-my-computer.py` from "
            f"{COURSE_KIT_NAME} with .venv active for the full check."
        )
    else:
        lines.append(
            "This computer is ready. Open the course folder and follow "
            "START-HERE.md to begin Session 1."
        )
    return "\n".join(lines) + "\n"


def main(argv=None, stream=None) -> int:
    """Run the readiness check and print its result. Exit 0 only when it passed."""
    parser = argparse.ArgumentParser(
        description="Check whether this computer and Course Kit are ready for Explore Studio."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="course folder to check (defaults to the current folder)",
    )
    parser.add_argument(
        "--computer-only",
        action="store_true",
        help="check only this computer, before the course is installed (never prints READY)",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="with --computer-only, skip the internet check when offline on purpose",
    )
    args = parser.parse_args(argv)

    network_probe = None
    if args.skip_network:

        def network_probe() -> tuple[bool, str]:
            return True, "skipped at your request"

    workspace = (args.workspace or Path.cwd()).resolve()
    results = run_checks(
        workspace=workspace,
        computer_only=args.computer_only,
        network_probe=network_probe,
    )
    print(format_report(results, args.computer_only), end="", file=stream or sys.stdout)
    banner = overall_result(results, args.computer_only)
    return 0 if banner in {READY_BANNER, COMPUTER_ONLY_BANNER} else 1


if __name__ == "__main__":
    raise SystemExit(main())
