"""Validate a reviewed candidate BEFORE replacing the one allowed public ZIP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.course_release import (
    PUBLIC,
    ROOT,
    ReleaseError,
    clean_source,
    git,
    load_contract,
    publication_diff,
    validate_candidate,
    verify_artifact,
)


def publish(candidate: Path, expected_sha: str, runtime: str, root: Path = ROOT) -> None:
    clean_source(root)
    contract = load_contract(root)
    if expected_sha != contract["expected_course_kit_sha256"]:
        raise ReleaseError("WRONG_CANDIDATE_SHA: argument differs from approved release contract")
    if runtime != contract["expected_runtime_pin"]:
        raise ReleaseError("WRONG_RUNTIME_PIN: argument differs from approved release contract")
    # Read once; publish exactly the bytes inspected, avoiding a source-file race.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="publication-check-") as tmp:
        checked = Path(tmp) / "candidate.zip"
        payload = candidate.read_bytes()
        checked.write_bytes(payload)
        verify_artifact(checked, contract)
        validate_candidate(contract, root)
    if git(root, "rev-parse", "HEAD") != git(root, "rev-parse", "origin/main"):
        raise ReleaseError(
            "STALE_PUBLICATION_BASE: fetch main and start the publication branch at origin/main"
        )
    (root / PUBLIC).write_bytes(payload)
    publication_diff(git(root, "diff", "--name-only", "HEAD").splitlines())
    print(
        "Prepared ZIP-only publication diff. Require independent exact-head review "
        "and owner merge approval."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--runtime-pin", required=True)
    args = parser.parse_args()
    try:
        publish(args.candidate, args.expected_sha, args.runtime_pin)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
