"""Parallel Python progression and publication boundary, including real rendering.

Set JOURNEY_SITE_OUT=course4teen-website/out after a fresh Next build to also
check the exported pages, RSC payloads, and browser JavaScript bundles.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from html import unescape
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
WEBSITE = ROOT / "course4teen-website"
DATA = WEBSITE / "lib/pythonJourney.ts"
COMPONENT = WEBSITE / "app/components/PythonJourney.tsx"
PUBLISHED = [f"S{i:02}" for i in range(1, 7)]
TOPICS = [
    "Output and strings", "Variables and basic types", "f-strings", "Functions",
    "Lists", "Dictionaries and loops", "Boolean state", "if / else",
    "Counters and loops", "Comparisons and assertions", "Boolean AND", "Boolean OR",
    "Boolean NOT", "Reuse and refactoring", "Decomposition and state tracing",
    "Deeper data traversal", "Searching and filtering", "Aggregation",
    "Sorting and flattening", "Data pipeline", "Defensive validation",
    "Debugging method", "Modular design", "Dictionaries as indexes and optimization",
    "Integration", "Program design", "Function contracts and nested data",
    "File I/O and deterministic generation", "Review and refactoring",
    "Explain and present a system",
]


def source_steps() -> dict:
    source = DATA.read_text()
    payload = source.split("const pythonJourneySteps: Record<string, PythonJourneyStep> = ", 1)[1].split(";", 1)[0]

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f"Duplicate source key: {key}"
            result[key] = value
        return result

    return json.loads(payload, object_pairs_hook=unique_keys)


def probe(**request) -> dict:
    completed = subprocess.run(
        ["node", str(Path(__file__).with_name("python_journey_probe.mjs"))],
        input=json.dumps(request), text=True, capture_output=True, cwd=ROOT, check=True,
    )
    return json.loads(completed.stdout)


@pytest.fixture(scope="module")
def rendered():
    if not shutil.which("node") or not (WEBSITE / "node_modules/react-dom").is_dir():
        pytest.skip("needs Node and website node_modules")
    return probe()


def visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def panel(html: str) -> str:
    found = re.findall(r'<aside\b[^>]*class="python-journey [^"]*".*?</aside>', html, flags=re.S)
    assert len(found) == 1
    return found[0]


def assert_steps(html: str, ids: list[str]) -> None:
    assert re.findall(r'data-python-step="([^"]+)"', html) == ids
    assert re.findall(r'data-python-current="([^"]+)"', html) == ids[-1:]
    assert html.count('aria-current="step"') == 1
    assert 'aria-label="Python Journey so far"' in html
    assert re.search(rf"{len(ids)}\s*/\s*30", visible(html))
    assert "You are here" in visible(html)


def test_all_30_canonical_steps_exist_once_and_have_objectives():
    steps = source_steps()
    assert list(steps) == [f"S{i:02}" for i in range(1, 31)]
    assert [step["id"] for step in steps.values()] == list(steps)
    assert [step["topic"] for step in steps.values()] == TOPICS
    for step in steps.values():
        assert step["capability"].strip()
        assert step["concepts"] and all(concept.strip() for concept in step["concepts"])
    assert steps["S01"]["capability"] == "Store observations as text and print them."
    assert steps["S06"]["capability"] == "Model structured records and process a collection with one loop."
    assert {"dictionaries", "for loop", "list of dictionaries", "KeyError"} <= set(steps["S06"]["concepts"])


def test_published_steps_follow_sessions_with_slides(rendered):
    assert rendered["publication"] == PUBLISHED
    assert [step["id"] for step in rendered["published"]] == rendered["publication"]
    assert rendered["total"] == 30
    assert rendered["current"]["id"] == "S06"
    assert rendered["current"]["topic"] == "Dictionaries and loops"
    assert_steps(rendered["full"], PUBLISHED)


def test_no_unpublished_objectives_or_contexts_are_rendered(rendered):
    for sid in ("S07", "S30", "unknown"):
        assert rendered["compact"][sid] == ""
        assert rendered["histories"][sid] == []
    for html in [rendered["full"], *rendered["compact"].values()]:
        for step in list(source_steps().values())[6:]:
            assert step["topic"] not in unescape(html)
            assert step["capability"] not in unescape(html)
        assert "Boolean" not in html
        assert "False → True → False" not in unescape(html)


@pytest.mark.parametrize("sid", PUBLISHED)
def test_compact_history_stops_at_the_current_session(rendered, sid):
    ids = PUBLISHED[:PUBLISHED.index(sid) + 1]
    html = rendered["compact"][sid]
    assert_steps(html, ids)
    assert [step["id"] for step in rendered["histories"][sid]] == ids
    assert "Python Journey so far" in visible(html)
    assert "Now I can…" in visible(html)
    assert re.search(r'href="/students/journey/?#python-journey"', html)
    concepts = html.split('aria-label="Key concepts this session">', 1)[1].split("</ul>", 1)[0]
    assert 2 <= concepts.count("<li") <= 4
    assert source_steps()[sid]["capability"] in visible(html)
    for step in list(source_steps().values())[len(ids):]:
        assert step["topic"] not in unescape(html)
        assert step["capability"] not in unescape(html)


def test_s06_features_dictionaries_and_for_loops(rendered):
    assert "dictionaries" in visible(rendered["compact"]["S06"])
    assert "for loop" in visible(rendered["compact"]["S06"])


def test_a_later_release_reveals_s07_only_when_published(rendered):
    # Mutate publication in a separate Node process; never edit the real calendar.
    future = probe(published=[*PUBLISHED, "S07"], sessions=["S01", "S06", "S07", "S08"])
    assert future["current"]["id"] == "S07"
    assert_steps(future["full"], [*PUBLISHED, "S07"])
    assert "Boolean state" in future["compact"]["S07"]
    assert future["compact"]["S08"] == ""
    assert future["compact"]["S01"] == rendered["compact"]["S01"]
    assert future["compact"]["S06"] == rendered["compact"]["S06"]


@pytest.mark.parametrize("sid", PUBLISHED)
def test_all_published_slides_use_the_shared_companion_panel(sid):
    page = (WEBSITE / f"app/students/slides/{sid.lower()}/page.tsx").read_text()
    assert '<PythonJourney session={session.id} mode="compact" />' in page
    companions = page.split('className="journey-companions">', 1)[1].split("</div>", 1)[0]
    assert "<JourneyContext" in companions and "<PythonJourney" in companions
    assert page.count("<PythonJourney") == 1


def test_shared_learn_page_and_main_journey_integrations():
    learn = (WEBSITE / "app/students/learn/[session]/page.tsx").read_text()
    assert "What we learned in Python" in learn
    assert '<PythonJourney session={session.id} mode="compact" />' in learn
    assert learn.index("<PythonJourney") < learn.index('className="section slide-deck"')
    main = (WEBSITE / "app/students/journey/page.tsx").read_text()
    assert "Two journeys, one course." in main
    assert "Explorer Journey" in main and "Python Journey" in main
    assert "<JourneyMap" in main and '<PythonJourney mode="full" />' in main
    assert 'id="python-journey"' in main


def test_mobile_layout_keeps_a_readable_vertical_list():
    css = (WEBSITE / "app/globals.css").read_text()
    assert ".journey-companions { display: grid; grid-template-columns: minmax(0, 1fr);" in css
    assert "@media (min-width: 900px)" in css
    assert ".journey-companions > * { min-width: 0;" in css
    assert "overflow-wrap: anywhere;" in css
    assert ".python-journey-link:focus-visible" in css
    assert '"use client"' not in COMPONENT.read_text()


SITE_OUT = os.environ.get("JOURNEY_SITE_OUT")
needs_site = pytest.mark.skipif(not SITE_OUT, reason="set JOURNEY_SITE_OUT to a fresh Next export")


@needs_site
def test_fresh_build_journey_has_exactly_s01_through_s06():
    html = (ROOT / SITE_OUT / "students/journey/index.html").read_text()
    assert "Two journeys, one course." in visible(html)
    assert "Explorer Journey" in visible(html) and "Python Journey" in visible(html)
    assert_steps(panel(html), PUBLISHED)
    assert "Boolean state" not in html and "Boolean AND" not in html
    for step in list(source_steps().values())[6:]:
        assert step["topic"] not in unescape(panel(html))
        assert step["capability"] not in unescape(html)
    assert "Next: coming soon" in visible(panel(html))
    assert not (ROOT / SITE_OUT / "students/slides/s07/index.html").exists()
    assert not (ROOT / SITE_OUT / "students/learn/s07/index.html").exists()


@needs_site
@pytest.mark.parametrize("sid", PUBLISHED)
@pytest.mark.parametrize("kind", ["slides", "learn"])
def test_fresh_build_session_context_has_no_later_objectives(sid, kind):
    html = (ROOT / SITE_OUT / f"students/{kind}/{sid.lower()}/index.html").read_text()
    context = panel(html)
    ids = PUBLISHED[:PUBLISHED.index(sid) + 1]
    assert_steps(context, ids)
    assert "World Journey" in visible(html)
    assert "Boolean state" not in html
    for step in list(source_steps().values())[len(ids):]:
        assert step["topic"] not in unescape(context)
        assert step["capability"] not in unescape(html)  # includes RSC payloads
    assert html.index("data-python-current") < html.index('class="section slide-deck"')


@needs_site
def test_future_curriculum_never_ships_in_browser_bundles():
    scripts = list((ROOT / SITE_OUT / "_next/static").rglob("*.js"))
    assert scripts
    for path in scripts:
        source = path.read_text()
        for step in list(source_steps().values())[6:]:
            assert step["capability"] not in source, path
        assert "Boolean state" not in source, path
