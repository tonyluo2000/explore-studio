"""Create a student's own ``my-explore-world`` folder without touching existing work.

Students run this from the Course Kit folder, starting in Session 2:

```console
python3 make-my-world.py
```

The Course Kit (``explore-studio-course``) is replaceable: a teacher may hand
out a newer copy at any time. The Student Workspace this command creates
(``my-explore-world``, next to the Course Kit by default) belongs to the
student and must survive every Course Kit update. So this command:

- creates only files that are missing, and never overwrites an existing file;
- is safe to run again, which is how a student recovers a deleted template;
- refuses to create the workspace inside the Course Kit, where a kit update
  would replace it;
- uses only the Python standard library and needs no Git, account, or network.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

WORKSPACE_NAME = "my-explore-world"
TEMPLATE_DIR_NAME = "my-world-template"
KIT_MARKERS = ("START-HERE.md", "course-materials.json")


class WorkspaceError(ValueError):
    """The requested workspace location is not safe for student work."""


def default_template_root() -> Path:
    """Return the template next to this script in the kit, or in a source checkout."""
    here = Path(__file__).resolve().parent
    kit_template = here / TEMPLATE_DIR_NAME
    if kit_template.is_dir():
        return kit_template
    return here.parent / "classroom" / TEMPLATE_DIR_NAME


def default_workspace_root() -> Path:
    """Return ``my-explore-world`` beside the folder that holds this script."""
    return Path(__file__).resolve().parent.parent / WORKSPACE_NAME


def _find_course_kit(path: Path) -> Path | None:
    """Return the Course Kit folder that contains ``path``, if any."""
    for candidate in (path, *path.parents):
        if all((candidate / marker).is_file() for marker in KIT_MARKERS):
            return candidate
    return None


def make_my_world(workspace_root=None, template_root=None) -> dict:
    """Copy every missing template file into the workspace; keep every existing file.

    Returns a receipt listing the workspace path and the relative paths that
    were created and kept.
    """
    workspace = Path(workspace_root).resolve() if workspace_root else default_workspace_root()
    template = Path(template_root).resolve() if template_root else default_template_root()

    if not template.is_dir():
        raise WorkspaceError(f"cannot find the {TEMPLATE_DIR_NAME} folder at {template}")
    if workspace.exists() and not workspace.is_dir():
        raise WorkspaceError(f"{workspace} exists and is not a folder")
    kit = _find_course_kit(workspace)
    if kit is not None:
        raise WorkspaceError(
            f"{workspace} is inside the course folder {kit}; a course update would "
            "replace it. Put your world next to the course folder instead."
        )
    if template == workspace or template in workspace.parents:
        raise WorkspaceError("the workspace must not be inside the template folder")

    created: list[str] = []
    kept: list[str] = []
    for source in sorted(path for path in template.rglob("*") if path.is_file()):
        relative = source.relative_to(template)
        if "__pycache__" in relative.parts or relative.name == ".DS_Store":
            continue
        destination = workspace / relative
        if destination.exists() or destination.is_symlink():
            kept.append(relative.as_posix())
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        created.append(relative.as_posix())
    return {"workspace": workspace, "created": created, "kept": kept}


def main(argv=None) -> int:
    """Run the student command."""
    parser = argparse.ArgumentParser(
        description="Create your own my-explore-world folder. Existing files are never replaced."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        type=Path,
        help=f"where to put your world (default: {WORKSPACE_NAME} next to the course folder)",
    )
    args = parser.parse_args(argv)
    try:
        receipt = make_my_world(args.folder)
    except WorkspaceError as error:
        print(f"Stopped: {error}", file=sys.stderr)
        return 1
    print(f"Your world folder: {receipt['workspace']}")
    for relative in receipt["created"]:
        print(f"  created  {relative}")
    for relative in receipt["kept"]:
        print(f"  kept     {relative}  (already yours, not changed)")
    print("Open explorer.py and companion.py there and make them your own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
