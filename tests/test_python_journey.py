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
PUBLISHED = [f"S{i:02}" for i in range(1, 8)]
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
    opening = re.search(r'<(aside|div)\b[^>]*class="python-journey [^"]*"[^>]*>', html)
    assert opening
    tag = opening.group(1)
    depth = 1
    for token in re.finditer(rf'</?{tag}\b[^>]*>', html[opening.end():]):
        depth += -1 if token.group().startswith("</") else 1
        if depth == 0:
            return html[opening.start():opening.end() + token.end()]
    raise AssertionError("Unclosed Python Journey panel")


def assert_steps(html: str, ids: list[str], *, cumulative_count: int | None = None) -> None:
    assert re.findall(r'data-python-step="([^"]+)"', html) == ids
    assert re.findall(r'data-python-current="([^"]+)"', html) == ids[-1:]
    assert html.count('aria-current="step"') == 1
    assert '<ol class="python-journey-steps" role="list"' in html
    assert 'aria-label="Python Journey so far"' not in html
    assert re.search(rf"{cumulative_count or len(ids)}\s*/\s*30", visible(html))
    assert "You are here" in visible(html)


def test_all_30_canonical_steps_exist_once_and_have_objectives():
    steps = source_steps()
    assert list(steps) == [f"S{i:02}" for i in range(1, 31)]
    assert [step["id"] for step in steps.values()] == list(steps)
    assert [step["topic"] for step in steps.values()] == TOPICS
    for step in steps.values():
        assert step["capability"].strip()
        assert step["concepts"] and all(concept.strip() for concept in step["concepts"])
    assert steps["S01"]["capability"] == "Record observations as text and print them."
    assert steps["S06"]["capability"] == "Model structured records and process a collection with one loop."
    assert {"dictionaries", "for loop", "list of dictionaries", "KeyError"} <= set(steps["S06"]["concepts"])


def test_published_steps_follow_sessions_with_slides(rendered):
    assert rendered["publication"] == PUBLISHED
    assert [step["id"] for step in rendered["published"]] == rendered["publication"]
    assert rendered["total"] == 30
    assert rendered["current"]["id"] == "S07"
    assert rendered["current"]["topic"] == "Boolean state"
    assert_steps(rendered["full"], PUBLISHED)


def test_no_unpublished_objectives_or_contexts_are_rendered(rendered):
    for sid in ("S08", "S30", "unknown"):
        assert rendered["compact"][sid] == ""
        assert rendered["histories"][sid] == []
    for html in [rendered["full"], *rendered["compact"].values()]:
        for step in list(source_steps().values())[7:]:
            assert step["topic"] not in unescape(html)
            assert step["capability"] not in unescape(html)
        assert "Boolean branches" not in html


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


def test_s07_release_preserves_previous_session_histories(rendered):
    previous = probe(published=PUBLISHED[:-1], sessions=PUBLISHED)
    assert previous["compact"]["S07"] == ""
    for sid in PUBLISHED[:-1]:
        assert previous["compact"][sid] == rendered["compact"][sid]
    assert "Boolean state" in rendered["compact"]["S07"]
    assert_steps(rendered["compact"]["S07"], PUBLISHED)


@pytest.fixture(scope="module")
def all_published(rendered):
    # Publication is simulated in the probe process only. The real site stays S07.
    ids = [f"S{i:02}" for i in range(1, 31)]
    return probe(published=ids, sessions=ids)


@pytest.mark.parametrize("count", range(1, 31))
def test_compact_history_is_bounded_and_session_local(all_published, count):
    sid = f"S{count:02}"
    html = all_published["compact"][sid]
    start = 1 if count <= 8 else count - 4
    ids = [f"S{i:02}" for i in range(start, count + 1)]
    assert_steps(html, ids, cumulative_count=count)
    if count <= 8:
        assert "earlier Python steps" not in html
        assert 'start="' not in html
    else:
        assert f"+ {count - 5} earlier Python steps" in visible(html)
        assert f'start="{start}"' in html
    assert visible(html).count("Python Journey so far") == 1
    for step in list(source_steps().values())[count:]:
        assert step["topic"] not in unescape(html)
        assert step["capability"] not in unescape(html)


def test_full_history_is_never_bounded(all_published):
    assert_steps(all_published["full"], [f"S{i:02}" for i in range(1, 31)])
    assert "earlier Python steps" not in all_published["full"]


def test_long_history_still_rejects_unpublished_sessions(rendered):
    ids = [f"S{i:02}" for i in range(1, 21)]
    future = probe(published=ids, sessions=["S20", "S21", "S30"])
    assert_steps(future["compact"]["S20"], ids[-5:], cumulative_count=20)
    assert future["compact"]["S21"] == future["compact"]["S30"] == ""
    for html in [future["full"], future["compact"]["S20"]]:
        for step in list(source_steps().values())[20:]:
            assert step["topic"] not in unescape(html)
            assert step["capability"] not in unescape(html)


def test_history_heading_is_not_repeated_as_a_list_label(rendered):
    html = rendered["compact"]["S06"]
    assert html.count("Python Journey so far") == 1
    assert '<ol class="python-journey-steps" role="list">' in html


def test_full_history_is_primary_content_inside_the_existing_section(rendered):
    assert rendered["full"].startswith('<div class="python-journey python-journey-full"')
    assert "<aside" not in rendered["full"]
    assert "Published Python Journey" not in rendered["full"]
    assert "<h2>What we can do with Python</h2>" in rendered["full"]


def test_explorer_track_naming_is_consistent():
    context = (WEBSITE / "app/components/JourneyContext.tsx").read_text()
    assert '>Explorer Journey</p>' in context
    for path in (WEBSITE / "app").rglob("*.tsx"):
        assert "World Journey" not in path.read_text(), path


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
def test_fresh_build_journey_has_exactly_s01_through_s07():
    html = (ROOT / SITE_OUT / "students/journey/index.html").read_text()
    assert "Two journeys, one course." in visible(html)
    assert "Explorer Journey" in visible(html) and "Python Journey" in visible(html)
    assert_steps(panel(html), PUBLISHED)
    assert panel(html).startswith('<div class="python-journey python-journey-full"')
    assert "Boolean state" in html and "Boolean AND" not in html
    for step in list(source_steps().values())[7:]:
        assert step["topic"] not in unescape(panel(html))
        assert step["capability"] not in unescape(html)
    assert "Next: coming soon" in visible(panel(html))
    assert not (ROOT / SITE_OUT / "students/slides/s08/index.html").exists()
    assert not (ROOT / SITE_OUT / "students/learn/s08/index.html").exists()


@needs_site
@pytest.mark.parametrize("sid", PUBLISHED)
@pytest.mark.parametrize("kind", ["slides", "learn"])
def test_fresh_build_session_context_has_no_later_objectives(sid, kind):
    html = (ROOT / SITE_OUT / f"students/{kind}/{sid.lower()}/index.html").read_text()
    context = panel(html)
    ids = PUBLISHED[:PUBLISHED.index(sid) + 1]
    assert_steps(context, ids)
    assert "Explorer Journey" in visible(html)
    assert "World Journey" not in visible(html)
    assert ("Boolean state" in html) is (sid == "S07")
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
        for step in list(source_steps().values())[7:]:
            assert step["capability"] not in source, path
        assert "Boolean branches" not in source, path
