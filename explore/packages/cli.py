"""Command-line interface for local Explorer Package workflows."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from explore.packages.classroom_trail import (
    DEFAULT_CLASSROOM_TRAIL_MISSION_ID,
    plan_local_classroom_trail,
    run_classroom_trail,
)
from explore.packages.contribution_models import PackageLoadResult
from explore.packages.explorer_package_export import (
    export_explorer_package,
    serialize_explorer_package_export_result,
)
from explore.packages.loader import load_explorer_package


def _validation_json(result: PackageLoadResult) -> str:
    report = result.validation_report
    manifest = report.manifest
    document = {
        "valid": result.is_loaded,
        "package": (
            None
            if manifest is None
            else {
                "id": manifest.package.id,
                "version": manifest.package.version,
                "student_api_version": manifest.compatibility.student_api,
            }
        ),
        "issues": [
            {
                "code": issue.code.value,
                "message": issue.message,
                "location": issue.location,
            }
            for issue in result.all_issues
        ],
    }
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="explore-package",
        description="Validate, export, and locally explore declarative Explorer Packages.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one unpacked package")
    validate.add_argument("package_root", type=Path)
    validate.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    export = commands.add_parser("export", help="write one deterministic package archive")
    export.add_argument("package_root", type=Path)
    export.add_argument("--output", type=Path, required=True, help="canonical archive path")
    export.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    trail = commands.add_parser("trail", help="run a local multi-package Classroom Trail")
    trail.add_argument("package_roots", type=Path, nargs="+")
    trail.add_argument(
        "--player",
        required=True,
        help="package-qualified character ID to control (for example student:hero)",
    )
    trail.add_argument("--name", default="Classroom Trail", help="local window title")
    trail.add_argument(
        "--mission-id",
        default=DEFAULT_CLASSROOM_TRAIL_MISSION_ID,
        help="exact canonical course mission ID",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local package command and return a process exit status."""
    args = _parser().parse_args(argv)
    if args.command == "validate":
        package_root = args.package_root.resolve()
        result = load_explorer_package(package_root)
        if args.json:
            print(_validation_json(result))
        elif result.is_loaded:
            assert result.package is not None
            print(f"valid: {result.package.metadata.id} " f"{result.package.metadata.version}")
        else:
            for issue in result.all_issues:
                print(f"{issue.code.value}: {issue.location}: {issue.message}")
        return 0 if result.is_loaded else 1

    if args.command == "trail":
        result = plan_local_classroom_trail(
            (package_root.resolve() for package_root in args.package_roots),
            player_qualified_id=args.player,
        )
        if not result.is_planned:
            for issue in result.issues:
                print(f"{issue.code.value}: {issue.location}: {issue.message}")
            return 1
        assert result.plan is not None
        run_classroom_trail(result.plan, name=args.name, mission_id=args.mission_id)
        return 0

    package_root = args.package_root.resolve()
    result = export_explorer_package(package_root, args.output.resolve())
    if args.json:
        print(serialize_explorer_package_export_result(result), end="")
    elif result.is_exported:
        assert result.artifact is not None and result.digest is not None
        print(
            f"exported: {result.artifact.package_id} {result.artifact.package_version} "
            f"sha256:{result.digest.hex_digest}"
        )
    else:
        for issue in result.issues:
            print(f"{issue.code.value}: {issue.location}: {issue.message}")
    return 0 if result.is_exported else 1


if __name__ == "__main__":
    raise SystemExit(main())
