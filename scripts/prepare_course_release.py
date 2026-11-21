"""Prepare a deterministic release bundle without publishing, pushing or merging."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_student_zip import build_student_zip
from scripts.course_release import (
    CONTRACT,
    PUBLIC,
    ROOT,
    ReleaseError,
    clean_source,
    compare_builds,
    git,
    inspect_zip,
    load_contract,
    published_sessions,
    rebuild_from_commit,
    validate_candidate,
)


def prepare(session: str, root: Path = ROOT, *, export_approved: bool = False) -> dict:
    clean_source(root)
    if session != published_sessions()[-1]:
        raise ReleaseError("SESSION_MISMATCH: use the current website published session")
    head = git(root, "rev-parse", "HEAD")
    output = root / "build/course-releases" / head
    output.mkdir(parents=True, exist_ok=True)
    first, second = output / "explore-studio-course.zip", output / "repeat.zip"
    if export_approved:
        contract = load_contract(root)
        rebuild_from_commit(contract["materials_provenance"], root, first)
        rebuild_from_commit(contract["materials_provenance"], root, second)
    else:
        build_student_zip(first, root)
        build_student_zip(second, root)
        contract = {
            "schema_version": 1,
            "published_session": session,
            "implementation_head": head,
            **inspect_zip(first),
        }
    compare_builds(first, second)
    validate_candidate(contract, root)
    second.unlink()
    if not export_approved:
        (root / CONTRACT).write_text(json.dumps(contract, indent=2) + "\n")
    metadata = {
        "candidate": first.relative_to(root).as_posix(),
        "runtime_changed": inspect_zip(root / PUBLIC)["expected_runtime_pin"]
        != contract["expected_runtime_pin"],
        "base": "main",
        "branch": f"codex/publish-course-kit-{head[:12]}",
        "title": f"Publish verified Course Kit for {session}",
        "allowed_files": [PUBLIC.as_posix()],
        "commands_after_implementation_merge": [
            "git fetch origin main",
            f"git switch -c codex/publish-course-kit-{head[:12]} origin/main",
            "python scripts/prepare_course_kit_publication.py --candidate "
            f"{first.relative_to(root).as_posix()} "
            f"--expected-sha {contract['expected_course_kit_sha256']} "
            f"--runtime-pin {contract['expected_runtime_pin']}",
            f"git add {PUBLIC.as_posix()}",
            f"git commit -m 'Publish verified {session} Course Kit'",
            f"git push -u origin codex/publish-course-kit-{head[:12]}",
            f"gh pr create --base main --title 'Publish verified Course Kit for {session}' "
            f"--body-file {output.relative_to(root).as_posix()}/publication-pr.md",
        ],
    }
    (output / "release-receipt.json").write_text(json.dumps(contract, indent=2) + "\n")
    (output / "publication.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "publication-pr.md").write_text(
        f"Publish the independently reviewed {session} candidate. Risk: C. "
        "Do not auto-merge or deploy.\n\n"
        f"Materials: {contract['materials_provenance']}\n"
        f"Runtime: {contract['expected_runtime_pin']}\n"
        f"SHA256: {contract['expected_course_kit_sha256']}\n"
        f"Members: {contract['expected_course_kit_members']}\n\n"
        "Require independent review of the exact publication head before owner approval.\n"
        "Implementation merge alone does not establish classroom readiness.\n"
    )
    implementation = {
        "base": "main",
        "source_head": head,
        "title": f"Prepare {session} runtime and classroom release candidate",
        "required_contract": CONTRACT.as_posix(),
        "review": "Independent exact-head review before owner-authorized implementation merge",
        "commands": [
            f"git add {CONTRACT.as_posix()}",
            f"git commit -m 'Record {session} Course Kit release candidate'",
            "git push -u origin HEAD",
            f"gh pr create --base main --title 'Prepare {session} runtime and release candidate' "
            f"--body-file {output.relative_to(root).as_posix()}/implementation-pr.md",
        ],
    }
    (output / "implementation.json").write_text(json.dumps(implementation, indent=2) + "\n")
    (output / "implementation-pr.md").write_text(
        f"Prepare the {session} implementation and reproducible Course Kit candidate. Risk: C.\n\n"
        f"Source: {head}\nCandidate SHA256: {contract['expected_course_kit_sha256']}\n\n"
        "Require independent exact-head review. Production kit lag is explicit; classroom "
        "readiness remains BLOCKED until separately approved publication, live verification "
        "and isolated fresh-install acceptance. Do not auto-merge or deploy.\n"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument(
        "--export-approved",
        action="store_true",
        help="CI: export existing validated contract without changing it",
    )
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.session, export_approved=args.export_approved), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
