"""Report release readiness. Default/main is strict; PR context is diff-derived."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.course_release import PUBLIC, ROOT, check_phase, git, load_contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pr-base", help="CI-only: actual pull_request base SHA; classify using changed files"
    )
    args = parser.parse_args()
    try:
        contract = load_contract()
        files = (
            git(ROOT, "diff", "--name-only", f"{args.pr_base}...HEAD").splitlines()
            if args.pr_base
            else []
        )
        phase = (
            ("publication" if PUBLIC.as_posix() in files else "implementation")
            if args.pr_base
            else "main"
        )
        print(
            f"{contract['published_session']} / {phase}\nWebsite: published\n"
            f"Implementation source: {contract['implementation_head']}"
        )
        print(
            "Proposed artifact commit (not merge proof): "
            + git(ROOT, "log", "-1", "--format=%H", "--", PUBLIC.as_posix())
        )
        print(check_phase(contract, phase, files))
        return 0
    except (ValueError, AssertionError, OSError) as error:
        print(f"{error}\nClassroom readiness: BLOCKED", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
