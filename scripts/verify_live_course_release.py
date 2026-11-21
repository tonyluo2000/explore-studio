"""Download actual public bytes with cache busting; optionally install in isolation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import venv
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.course_release import (
    ROOT,
    ZIP_ROOT,
    ReleaseError,
    load_contract,
    published_head,
    validate_candidate,
    verify_artifact,
)

URL = "https://course4teen.com/downloads/explore-studio-course.zip"


def fresh_install(archive: Path) -> dict:
    import zipfile

    # Caller must validate archive first. No target or home is supplied by user.
    with tempfile.TemporaryDirectory(prefix="course-live-install-") as tmp:
        base = Path(tmp)
        home = base / "home"
        home.mkdir()
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")
        }
        env.update(
            HOME=str(home),
            USERPROFILE=str(home),
            PYTHONNOUSERSITE="1",
            SDL_VIDEODRIVER="dummy",
            SDL_AUDIODRIVER="dummy",
            EXPLORE_STUDIO_AUDIO="off",
        )
        with zipfile.ZipFile(archive) as z:
            z.extractall(home)
        kit = home / ZIP_ROOT
        venv.create(kit / ".venv", with_pip=True)
        python = kit / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

        def run(*args: str) -> None:
            subprocess.run([str(python), *args], cwd=kit, env=env, check=True, timeout=600)

        run(
            "-m", "pip", "--isolated", "install", "--no-cache-dir", "-r", "requirements-student.txt"
        )
        run("check-my-computer.py")
        harness = base / "acceptance"
        harness.mkdir()
        for name in ("trail_driver.py", "course_release_acceptance.py"):
            shutil.copyfile(ROOT / "scripts" / name, harness / name)
        run(str(harness / "course_release_acceptance.py"), str(kit))
        return {"fresh_install": "passed", "trail_acceptance": ["S06", "S07", "S08", "S09"]}


def verify_live(contract: dict, *, install: bool = False, opener=None) -> dict:
    if install and contract["published_session"] not in ("S06", "S07", "S08", "S09"):
        raise ReleaseError(
            "MISSING_TRAIL_ACCEPTANCE: add current session contract before classroom verification"
        )
    opener = opener or urllib.request.urlopen
    url = f"{URL}?course_release={contract['expected_course_kit_sha256']}&t={time.time_ns()}"
    request = urllib.request.Request(
        url, headers={"Cache-Control": "no-cache", "Pragma": "no-cache"}
    )
    with opener(request, timeout=90) as response:
        if response.status != 200:
            raise ReleaseError(f"LIVE_HTTP_ERROR: HTTP {response.status}")
        payload = response.read(32 * 1024 * 1024 + 1)
        headers = {
            k: response.headers.get(k)
            for k in ("Cache-Control", "Age", "ETag", "Last-Modified", "CF-Cache-Status")
        }
    if len(payload) > 32 * 1024 * 1024:
        raise ReleaseError("LIVE_ARCHIVE_TOO_LARGE")
    with tempfile.TemporaryDirectory(prefix="course-live-download-") as tmp:
        path = Path(tmp) / "live.zip"
        path.write_bytes(payload)
        actual = verify_artifact(path, contract, live=True)
        publication_head = published_head(contract)
        result = {
            "session": contract["published_session"],
            "release_state": "LIVE_VERIFIED" if publication_head else "BUILDING",
            "course_kit_publication_head": publication_head,
            "live_sha": "verified",
            "sha256": actual["expected_course_kit_sha256"],
            "runtime": actual["expected_runtime_pin"],
            "cache_headers": headers,
            "classroom_readiness": "BLOCKED",
        }
        if install:
            result.update(fresh_install(path))
            if publication_head:
                result.update(release_state="CLASSROOM_VERIFIED", classroom_readiness="READY")
            else:
                raise ReleaseError(
                    "PUBLICATION_NOT_MERGED: live bytes and install match, but approved "
                    "contract/ZIP merge on origin/main is unproven; fetch main and retry"
                )
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--install-smoke-test", action="store_true")
    args = parser.parse_args()
    try:
        contract = load_contract()
        if args.session != contract["published_session"]:
            raise ReleaseError("SESSION_MISMATCH: use current published session")
        validate_candidate(contract)
        print(json.dumps(verify_live(contract, install=args.install_smoke_test), indent=2))
    except (ValueError, AssertionError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"{error}\nClassroom readiness: BLOCKED\n")


if __name__ == "__main__":
    main()
