"""S09 publication, truthful Python exercise, and public S10 boundary."""

import os
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

import pytest

from scripts.journey_snapshots import SESSIONS_BY_ID, canonical_command, published_sessions
from tests.test_python_journey import probe, source_steps, visible

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "course4teen-website"
SLIDES = WEB / "app/students/slides/s09/page.tsx"


def test_publication_command_and_teaching_sequence():
    assert published_sessions() == tuple(f"S{i:02}" for i in range(1, 10))
    slides = SLIDES.read_text()
    command = canonical_command("S09")
    assert command.mission_id == "count-object-interactions"
    card = (ROOT / "lessons/sessions/s09/student/task-card.md").read_text()
    one_line = " ".join(
        line.strip().removesuffix("\\").strip()
        for line in card.split("explore-package trail ", 1)[1]
        .split("```", 1)[0]
        .strip()
        .splitlines()
    )
    assert "explore-package trail " + one_line.strip() in slides
    assert '<PythonJourney session={session.id} mode="compact" />' in slides
    assert "<JourneyContext session={session.id} />" in slides
    for term in (
        "integer",
        "count = count + 1",
        "off-by-one",
        "assert count == goal",
        "range(1, goal + 1)",
        "range(1, goal)",
        "does not execute inside Trail",
        "counter:",
        "goal: 3",
        "counter",
        "one spark short",
    ):
        assert term.lower() in slides.lower(), term
    assert slides.count("heading:") == 21  # type plus twenty slides
    assert not (WEB / "app/students/slides/s10").exists()
    assert not (WEB / "public/journey/s10").exists()
    assert "S10" not in SESSIONS_BY_ID


def test_worked_assertion_and_off_by_one_are_executable():
    learn = (WEB / "lib/learn.ts").read_text().split('id: "S09",', 1)[1]
    code = re.search(r"code: `([^`]*)`", learn).group(1)
    starter = (ROOT / "lessons/sessions/s09/student/starter.py").read_text()
    expected = "\n".join(line for line in starter.splitlines()[2:] if "# TODO:" not in line).strip()
    assert code == expected + "\n\nassert count == goal"
    correct = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert correct.returncode == 0 and correct.stdout == "1 1\n2 2\n3 3\n"
    broken = subprocess.run(
        [sys.executable, "-c", code.replace("goal + 1", "goal")], capture_output=True, text=True
    )
    assert broken.returncode != 0 and "AssertionError" in broken.stderr
    assert broken.stdout == "1 1\n2 2\n"


def test_s09_histories_are_bounded_and_previous_contexts_frozen():
    result = probe(sessions=["S06", "S07", "S08", "S09", "S10"])
    assert result["current"]["id"] == "S09"
    html = result["compact"]["S09"]
    assert re.findall(r'data-python-step="([^"]+)"', html) == ["S05", "S06", "S07", "S08", "S09"]
    assert "+ 4 earlier Python steps" in visible(html)
    assert "9 / 30" in visible(html)
    previous = probe(published=[f"S{i:02}" for i in range(1, 9)], sessions=["S06", "S07", "S08"])
    for sid in ("S06", "S07", "S08"):
        assert result["compact"][sid] == previous["compact"][sid]
    assert result["compact"]["S10"] == ""
    assert len(re.findall(r"data-python-step=", result["full"])) == 9


@pytest.mark.skipif(not os.environ.get("JOURNEY_SITE_OUT"), reason="needs fresh website export")
def test_public_html_rsc_metadata_and_javascript_exclude_future_details():
    out = ROOT / os.environ["JOURNEY_SITE_OUT"]
    for route in ("slides", "learn"):
        html = (out / f"students/{route}/s09/index.html").read_text()
        assert 'data-python-current="S09"' in html
        assert "9 / 30" in visible(html)
        assert not (out / f"students/{route}/s10").exists()
    forbidden = [
        "Comparisons and assertions",
        source_steps()["S10"]["capability"],
        "respond_to_counter",
        "when_at_or_above_goal",
        "/journey/s10/",
        "/students/slides/s10/",
        "/students/learn/s10/",
    ]
    for path in out.rglob("*"):
        if path.suffix not in (".html", ".txt", ".js", ".json"):
            continue
        text = unescape(path.read_text())
        for term in forbidden:
            assert term not in text, (path, term)
