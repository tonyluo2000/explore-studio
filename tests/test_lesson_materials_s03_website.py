"""S03 student website: slides and Python Notes stay grounded in the canonical lesson."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parents[1]
S03 = PROJECT_ROOT / "lessons" / "sessions" / "s03"
WEBSITE = PROJECT_ROOT / "course4teen-website"
SLIDES = WEBSITE / "app" / "students" / "slides" / "s03" / "page.tsx"
LEARN = WEBSITE / "lib" / "learn.ts"
CALENDAR = WEBSITE / "lib" / "calendar.ts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _s03_learn_entry() -> str:
    return _read(LEARN).split('id: "S03"', 1)[1]


def test_s03_is_published_in_the_slides_index_and_learn_route():
    assert re.search(r'sessionsWithSlides[^=]*= \[[^\]]*"S03"', _read(CALENDAR))
    assert 'id: "S03"' in _read(LEARN)
    slides = _read(SLIDES)
    assert 'canonical: "/students/slides/s03/"' in slides
    assert "/students/learn/s03/" in slides


def test_s03_slides_cover_the_canonical_mission_and_bridge():
    slides = _read(SLIDES)
    for required in (
        "make-your-object-respond",
        "object_name",
        "near_message",
        "interacted_message",
        "when_near",
        "when_interacted",
        "Moving near will show ___; pressing E will show ___.",
        "explore-package validate lessons/sessions/s03/student/explorer-package",
        '--mission-id "make-your-object-respond"',
        '--name "S03 Make the World React"',
        'f"The {object_name needle begins to shimmer."',
        "SyntaxError",
        "S04 · Introduce a Character",
    ):
        assert required in slides, required


def test_s03_slides_show_the_real_starter_and_its_unfinished_output():
    slides = _read(SLIDES)
    for line in _read(S03 / "student" / "starter.py").splitlines()[2:]:
        assert line in slides, line
    output = subprocess.run(
        [sys.executable, str(S03 / "student" / "starter.py")],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert output.strip() in slides


def test_s03_website_yaml_and_notes_match_the_package():
    compass = yaml.safe_load(_read(S03 / "student" / "explorer-package" / "objects" / "compass.yaml"))
    slides = _read(SLIDES)
    notes = _s03_learn_entry()
    for field in ("when_near", "when_interacted"):
        assert f'{field}: "{compass[field]}"' in slides
    assert compass["when_near"] in notes and compass["when_interacted"] in notes


def test_s03_slides_do_not_borrow_the_m02_only_visual_polish():
    slides = _read(SLIDES)
    assert "NovaPixelScene" not in slides
    assert "S02TrailMap" not in slides
    assert "standard Trail view, not the painted Moon" in slides


def test_s03_notes_name_their_real_course_kit_source():
    notes = _s03_learn_entry()
    assert 'sourceFile: "task-card.md"' in notes
    assert (S03 / "student" / "task-card.md").is_file()
    assert not (S03 / "student" / "python-notes.md").exists(), (
        "S03 now has python-notes.md; drop sourceFile so the Learn page points at it"
    )
    for required in (
        "f-string",
        "braces",
        "near vs. interacted",
        "python lessons/sessions/s03/student/starter.py",
        "SyntaxError",
    ):
        assert required in notes, required
