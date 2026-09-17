"""Verify the committed public student ZIP against the commit it claims.

The website ships a checked-in artifact:

``course4teen-website/public/downloads/explore-studio-course.zip``

Its embedded ``course-materials.json`` records a
``course_materials_source_commit``: the content commit whose materials the
archive was built from. Source tests and freshly built in-memory ZIPs can all
be green while that committed artifact is stale or was generated from the wrong
checkout, so this guard checks the only thing those tests cannot: that the
bytes on disk are exactly what the declared commit produces.

The rebuild always happens in an isolated detached worktree at the declared
provenance commit, never in the current checkout. Rebuilding from HEAD would
make the check circular -- it would prove the artifact matches whatever is
checked out now, not the commit it claims produced it.

```console
python3 scripts/verify_public_zip_provenance.py
```
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

if __package__ in (None, ""):  # allow `python3 scripts/verify_public_zip_provenance.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_student_zip import ZIP_NAME, ZIP_ROOT
from scripts.sync_student_downloads import DOWNLOADS_DIR

PUBLIC_ZIP_PATH = DOWNLOADS_DIR / ZIP_NAME
COURSE_MATERIALS_MEMBER = f"{ZIP_ROOT}/course-materials.json"
PROVENANCE_KEY = "course_materials_source_commit"
FULL_SHA_PATTERN = re.compile(r"\A[0-9a-f]{40}\Z")

#: Drift lines reported per mismatching member, so a failure names the file
#: that changed instead of only the archive digest.
MAX_REPORTED_DRIFT = 5


class ProvenanceGuardError(AssertionError):
    """The committed public ZIP does not match its declared provenance commit."""


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def read_declared_provenance(archive_path: Path) -> str:
    """Return the ``course_materials_source_commit`` recorded inside the ZIP."""
    archive_path = Path(archive_path)
    if not archive_path.is_file():
        raise ProvenanceGuardError(f"committed public ZIP is missing: {archive_path}")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            raw = archive.read(COURSE_MATERIALS_MEMBER)
    except KeyError as error:
        raise ProvenanceGuardError(
            f"committed public ZIP has no {COURSE_MATERIALS_MEMBER} member"
        ) from error
    except zipfile.BadZipFile as error:
        raise ProvenanceGuardError(
            f"committed public ZIP is not a readable archive: {error}"
        ) from error
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProvenanceGuardError(
            f"{COURSE_MATERIALS_MEMBER} is not readable JSON: {error}"
        ) from error
    declared = manifest.get(PROVENANCE_KEY)
    if not isinstance(declared, str) or not declared:
        raise ProvenanceGuardError(f"{COURSE_MATERIALS_MEMBER} does not record {PROVENANCE_KEY}")
    return declared


def validate_provenance_commit(declared: str, repo_root: Path, head: str = "HEAD") -> str:
    """Raise unless ``declared`` is a full SHA resolving to an ancestor of ``head``.

    The ancestor rule is what ties the artifact to the branch under review: a
    ZIP built from a commit that is not reachable from HEAD was generated from
    some other checkout and says nothing about this branch's materials.
    """
    repo_root = Path(repo_root)
    if not FULL_SHA_PATTERN.match(declared):
        raise ProvenanceGuardError(
            f"{PROVENANCE_KEY} must be 40 lowercase hex characters, got {declared!r}"
        )
    resolved = _git(repo_root, "rev-parse", "--verify", "--quiet", f"{declared}^{{commit}}")
    if resolved.returncode != 0 or resolved.stdout.strip() != declared:
        raise ProvenanceGuardError(
            f"{PROVENANCE_KEY} {declared} does not resolve to a commit in this repository "
            "(if this is a real commit, check out with full history: fetch-depth: 0)"
        )
    head_sha = _git(
        repo_root, "rev-parse", "--verify", "--quiet", f"{head}^{{commit}}"
    ).stdout.strip()
    ancestry = _git(repo_root, "merge-base", "--is-ancestor", declared, head)
    if ancestry.returncode != 0:
        raise ProvenanceGuardError(
            f"{PROVENANCE_KEY} {declared} is not an ancestor of HEAD {head_sha or head}: "
            "the committed ZIP was built from a commit that is not on this branch"
        )
    return declared


def rebuild_from_commit(declared: str, repo_root: Path, destination: Path) -> Path:
    """Build the student ZIP from ``declared`` in a throwaway detached worktree.

    The worktree is the guard's whole point: the builder runs against exactly
    the tree of the provenance commit, so the current checkout -- which may
    carry the very content drift being looked for -- cannot influence the
    result.
    """
    repo_root = Path(repo_root).resolve()
    destination = Path(destination).resolve()
    with tempfile.TemporaryDirectory(prefix="zip-provenance-") as staging:
        worktree = Path(staging) / "source"
        added = _git(repo_root, "worktree", "add", "--detach", "--force", str(worktree), declared)
        if added.returncode != 0:
            raise ProvenanceGuardError(
                f"could not check out provenance commit {declared}: {added.stderr.strip()}"
            )
        try:
            builder = worktree / "scripts" / "build_student_zip.py"
            if not builder.is_file():
                raise ProvenanceGuardError(
                    f"provenance commit {declared} has no {builder.relative_to(worktree)}"
                )
            built = subprocess.run(
                [sys.executable, str(builder), str(destination)],
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
            )
            if built.returncode != 0 or not destination.is_file():
                raise ProvenanceGuardError(
                    f"rebuilding the student ZIP at {declared} failed: "
                    f"{(built.stderr or built.stdout).strip()}"
                )
        finally:
            shutil.rmtree(worktree, ignore_errors=True)
            _git(repo_root, "worktree", "prune")
    return destination


def _members(archive_path: Path) -> dict[str, str]:
    with zipfile.ZipFile(archive_path) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()}


def describe_drift(committed: Path, rebuilt: Path) -> list[str]:
    """Return human-readable lines naming the first members that differ."""
    try:
        committed_members = _members(Path(committed))
        rebuilt_members = _members(Path(rebuilt))
    except (zipfile.BadZipFile, OSError) as error:  # pragma: no cover - unreadable archive
        return [f"could not compare members: {error}"]
    lines: list[str] = []
    for name in sorted(set(committed_members) - set(rebuilt_members)):
        lines.append(f"only in committed ZIP: {name}")
    for name in sorted(set(rebuilt_members) - set(committed_members)):
        lines.append(f"only in rebuilt ZIP:   {name}")
    for name in sorted(set(committed_members) & set(rebuilt_members)):
        if committed_members[name] != rebuilt_members[name]:
            lines.append(f"content differs:       {name}")
    if len(lines) > MAX_REPORTED_DRIFT:
        hidden = len(lines) - MAX_REPORTED_DRIFT
        lines = lines[:MAX_REPORTED_DRIFT] + [f"... and {hidden} more differing member(s)"]
    if not lines:
        lines.append("members are identical; the archives differ in ZIP metadata or ordering")
    return lines


def compare_archives(committed: Path, rebuilt: Path, declared: str) -> dict:
    """Raise unless the two archives are byte, digest, and member-count equal."""
    committed = Path(committed)
    rebuilt = Path(rebuilt)
    committed_bytes = committed.read_bytes()
    rebuilt_bytes = rebuilt.read_bytes()
    committed_sha = hashlib.sha256(committed_bytes).hexdigest()
    rebuilt_sha = hashlib.sha256(rebuilt_bytes).hexdigest()
    with zipfile.ZipFile(committed) as archive:
        committed_count = len(archive.namelist())
    with zipfile.ZipFile(rebuilt) as archive:
        rebuilt_count = len(archive.namelist())

    if (
        committed_bytes == rebuilt_bytes
        and committed_sha == rebuilt_sha
        and committed_count == rebuilt_count
    ):
        return {
            "declared_provenance_commit": declared,
            "committed_sha256": committed_sha,
            "rebuilt_sha256": rebuilt_sha,
            "members": committed_count,
        }

    report = [
        "committed public student ZIP does not match its declared provenance commit",
        f"  declared {PROVENANCE_KEY}: {declared}",
        f"  committed ZIP sha256:     {committed_sha} ({committed_count} members)",
        f"  rebuilt  ZIP sha256:      {rebuilt_sha} ({rebuilt_count} members)",
        "  drift:",
        *(f"    {line}" for line in describe_drift(committed, rebuilt)),
        "",
        "Regenerate the artifact with: python3 scripts/sync_student_downloads.py",
        "then commit the refreshed ZIP so its provenance commit matches its bytes.",
    ]
    raise ProvenanceGuardError("\n".join(report))


def verify_public_zip_provenance(repo_root: Path | None = None, head: str = "HEAD") -> dict:
    """Verify the committed public ZIP end to end and return its receipt."""
    root = (
        Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[1]
    )
    archive_path = root / PUBLIC_ZIP_PATH
    declared = read_declared_provenance(archive_path)
    validate_provenance_commit(declared, root, head)
    with tempfile.TemporaryDirectory(prefix="zip-provenance-out-") as staging:
        rebuilt = rebuild_from_commit(declared, root, Path(staging) / ZIP_NAME)
        return compare_archives(archive_path, rebuilt, declared)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the committed public student ZIP against its provenance commit."
    )
    parser.add_argument(
        "--head", default="HEAD", help="revision the provenance must be an ancestor of"
    )
    args = parser.parse_args(argv)
    try:
        receipt = verify_public_zip_provenance(head=args.head)
    except ProvenanceGuardError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"verified {PUBLIC_ZIP_PATH}")
    print(f"  provenance commit: {receipt['declared_provenance_commit']}")
    print(f"  sha256:            {receipt['committed_sha256']}")
    print(f"  members:           {receipt['members']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
