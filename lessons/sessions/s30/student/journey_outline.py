"""Prepare an S30 presentation outline from the student's own ``journey.md``.

Students run this from the Course Kit folder near the end of the course:

```console
python3 lessons/sessions/s30/student/journey_outline.py
```

It reads ``my-explore-world/journey.md`` (My Explore Journey), never changes
it, and writes one separate file, ``my-explore-world/presentation-outline.md``.
The outline lists the student's own dated entries, in the order they were
written, under the six World Premiere questions. It copies the student's words
exactly and adds nothing: no summaries, no ranking, no "best" moment. The
student reads the outline and chooses what to present.

Only the Python standard library is used. No AI, account, or network.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_NAME = "my-explore-world"
JOURNEY_NAME = "journey.md"
OUTLINE_NAME = "presentation-outline.md"

FIELD_LABELS = ("Date", "Place", "Weather", "Explore-world location")
SECTION_HEADINGS = (
    "Today I built",
    "Python I learned",
    "My favorite moment",
    "A problem I solved",
    "My next idea",
)

#: The six World Premiere questions and the journal section each one draws on.
#: ``None`` means the whole entry list is the material (first vs. last entry).
PRESENTATION_QUESTIONS = (
    ("How did my world change from the beginning?", None),
    ("What am I most proud of?", "Today I built"),
    ("What was a difficult problem I solved?", "A problem I solved"),
    ("What is one important thing I learned about Python?", "Python I learned"),
    ("What was one memorable moment from my Journey?", "My favorite moment"),
    ("What would I build next?", "My next idea"),
)


class JourneyOutlineError(ValueError):
    """The outline could not be prepared without touching student work."""


@dataclass
class JourneyEntry:
    """One dated entry from ``journey.md``, kept in the student's own words."""

    title: str
    fields: dict[str, str] = field(default_factory=dict)
    sections: dict[str, list[str]] = field(default_factory=dict)

    def section_lines(self, heading: str) -> list[str]:
        return [line for line in self.sections.get(heading, []) if line.strip()]


def default_workspace_root() -> Path:
    """Return ``my-explore-world`` next to the Course Kit that holds this file."""
    kit_root = Path(__file__).resolve().parents[4]
    return kit_root.parent / WORKSPACE_NAME


def parse_journey(text: str) -> list[JourneyEntry]:
    """Return the entries in ``text`` in source order.

    An entry starts at a ``## `` heading outside a fenced code block, so the
    copyable template and the made-up example inside the seed file are not
    mistaken for real entries. Text before the first heading is ignored.
    """
    entries: list[JourneyEntry] = []
    current: JourneyEntry | None = None
    section: str | None = None
    in_fence = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            current = JourneyEntry(title=line[3:].strip())
            entries.append(current)
            section = None
            continue
        if current is None:
            continue
        if line.startswith("### "):
            section = line[4:].strip()
            current.sections.setdefault(section, [])
            continue
        if section is None:
            label, separator, value = line.partition(":")
            if separator and label.strip() in FIELD_LABELS:
                current.fields[label.strip()] = value.strip()
            continue
        current.sections[section].append(line)
    return entries


def _entry_lines(entry: JourneyEntry) -> list[str]:
    lines = [f"### {entry.title}"]
    for label in FIELD_LABELS:
        value = entry.fields.get(label, "")
        if value:
            lines.append(f"- {label}: {value}")
    for heading in SECTION_HEADINGS:
        body = entry.section_lines(heading)
        if body:
            lines.append(f"- {heading}:")
            lines.extend(f"  {line.strip()}" for line in body)
    lines.append("")
    return lines


def _describe(entry: JourneyEntry) -> str:
    date = entry.fields.get("Date", "")
    return f"{entry.title} ({date})" if date else entry.title


def render_outline(entries: list[JourneyEntry]) -> str:
    """Return the deterministic outline text for ``entries``."""
    lines = [
        "# My Presentation Outline",
        "",
        f"Prepared from `{WORKSPACE_NAME}/{JOURNEY_NAME}` (My Explore Journey).",
        "The journal was read, not changed. Every line below in the timeline is",
        "copied from my own entries, in the order I wrote them. Nothing was",
        "added, summarized, or ranked. I choose what to present.",
        "",
        "This file is mine to edit. Running the helper again only writes a new",
        "copy when this file is gone or when I ask it to replace this one.",
        "",
        "## Part 1 — My Journey, in order",
        "",
    ]
    if entries:
        for entry in entries:
            lines.extend(_entry_lines(entry))
    else:
        lines.extend(
            [
                f"No entries were found in {JOURNEY_NAME} yet. Add entries there, then",
                "run the helper again.",
                "",
            ]
        )
    lines.extend(["## Part 2 — The six presentation questions", ""])
    for number, (question, heading) in enumerate(PRESENTATION_QUESTIONS, start=1):
        lines.append(f"### {number}. {question}")
        lines.append("")
        if heading is None:
            if len(entries) >= 2:
                lines.append(f"Look at my first entry, {_describe(entries[0])}, and my")
                lines.append(f"last entry, {_describe(entries[-1])}. What is different?")
            elif len(entries) == 1:
                lines.append(f"I have one entry so far: {_describe(entries[0])}.")
            else:
                lines.append("I have no entries yet.")
        else:
            lines.append(f'From my "{heading}" lines, in order:')
            lines.append("")
            found = False
            for entry in entries:
                for line in entry.section_lines(heading):
                    lines.append(f"- {_describe(entry)}: {line.strip()}")
                    found = True
            if not found:
                lines.append("- (none written yet)")
        lines.append("")
        lines.append("My choice:")
        lines.append("")
        lines.append("What I will say:")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def prepare_outline(workspace_root=None, replace: bool = False) -> dict:
    """Read the journal, write the outline, and return a small receipt.

    Raises:
        JourneyOutlineError: If the workspace or journal is missing, or the
            outline already exists and ``replace`` is False.
    """
    workspace = Path(workspace_root).resolve() if workspace_root else default_workspace_root()
    journey = workspace / JOURNEY_NAME
    outline = workspace / OUTLINE_NAME
    if not workspace.is_dir():
        raise JourneyOutlineError(
            f"cannot find your {WORKSPACE_NAME} folder at {workspace}; "
            "run make-my-world.py first"
        )
    if not journey.is_file():
        raise JourneyOutlineError(
            f"cannot find {JOURNEY_NAME} in {workspace}; run make-my-world.py to add it"
        )
    if outline.exists() and not replace:
        raise JourneyOutlineError(
            f"{OUTLINE_NAME} already exists in {workspace}; rename it, or run again "
            "with --replace to write a fresh copy"
        )
    entries = parse_journey(journey.read_text(encoding="utf-8"))
    outline.write_text(render_outline(entries), encoding="utf-8")
    return {"journey": journey, "outline": outline, "entries": len(entries)}


def main(argv=None) -> int:
    """Run the student command."""
    parser = argparse.ArgumentParser(
        description=(
            f"Prepare {OUTLINE_NAME} from your {JOURNEY_NAME}. "
            "The journal is read only and never changed."
        )
    )
    parser.add_argument(
        "folder",
        nargs="?",
        type=Path,
        help=f"your world folder (default: {WORKSPACE_NAME} next to the course folder)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help=f"write a fresh {OUTLINE_NAME} even if one already exists",
    )
    args = parser.parse_args(argv)
    try:
        receipt = prepare_outline(args.folder, replace=args.replace)
    except JourneyOutlineError as error:
        print(f"Stopped: {error}", file=sys.stderr)
        return 1
    print(f"Read     {receipt['journey']}  ({receipt['entries']} entries, not changed)")
    print(f"Wrote    {receipt['outline']}")
    print("Open the outline, read your own entries, and choose what to present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
