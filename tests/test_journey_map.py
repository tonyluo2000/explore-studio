"""The student Journey Map (Course Journey Phase D): data model, progressive
reveal, the future-content boundary, and the site integration.

The reveal logic is the website's own TypeScript (``lib/journeyState.ts``). It
imports nothing, so ``tests/journey_map_probe.mjs`` runs it under Node's type
stripping against the committed data, or against a mutated copy, and these
tests check what it returns. Static checks read the TypeScript and JSON
directly. Set ``JOURNEY_SITE_OUT`` to a fresh ``next build`` output folder to
also check the rendered HTML.
"""

from __future__ import annotations

import copy
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
JOURNEY_JSON = WEBSITE / "journey" / "journey.json"
MANIFEST = WEBSITE / "journey" / "snapshots.json"
CALENDAR = WEBSITE / "lib" / "calendar.ts"
LEARN = WEBSITE / "lib" / "learn.ts"
JOURNEY_LIB = WEBSITE / "lib" / "journey.ts"
STATE_LIB = WEBSITE / "lib" / "journeyState.ts"
PAGE = WEBSITE / "app" / "students" / "journey" / "page.tsx"
MAP = WEBSITE / "app" / "components" / "JourneyMap.tsx"
CONTEXT = WEBSITE / "app" / "components" / "JourneyContext.tsx"
SLIDES_INDEX = WEBSITE / "app" / "students" / "slides" / "page.tsx"
LEARN_PAGE = WEBSITE / "app" / "students" / "learn" / "[session]" / "page.tsx"
HOME = WEBSITE / "app" / "page.tsx"
CSS = WEBSITE / "app" / "globals.css"
PROBE = Path(__file__).with_name("journey_map_probe.mjs")

JOURNEY_FILES = (JOURNEY_JSON, JOURNEY_LIB, STATE_LIB, PAGE, MAP, CONTEXT)

#: Story and places that belong to later sessions (curriculum S05 onward). None
#: may appear in Journey data or Journey code until that session is published.
LATER_STORY = (
    "Starlight",
    "garden",
    "Sky gate",
    "Sky Gate",
    "Storm",
    "Weather Reader",
    "observatory",
    "secret sequence",
    "guardian",
    "Curator",
    "Atlas",
    "Script a Conversation",
    "conversation",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _journey() -> dict:  # type: ignore[type-arg]
    return json.loads(_read(JOURNEY_JSON))


def _published() -> list[str]:
    match = re.search(r"sessionsWithSlides[^=]*= \[([^\]]*)\]", _read(CALENDAR))
    assert match
    return re.findall(r'"(S\d\d)"', match.group(1))


def _calendar() -> dict[str, dict[str, object]]:
    rows = re.findall(
        r'\{ id: "(S\d\d)", number: (\d+), date: "([\d-]+)", title: "([^"]+)" \}', _read(CALENDAR)
    )
    return {
        sid: {"id": sid, "number": int(n), "date": date, "title": title}
        for sid, n, date, title in rows
    }


def _learn_ids() -> list[str]:
    return re.findall(r'^\s+id: "(S\d\d)"', _read(LEARN), re.MULTILINE)


def _heroes() -> dict[str, dict]:  # type: ignore[type-arg]
    entries = json.loads(_read(MANIFEST))["snapshots"]
    return {entry["session"]: entry for entry in entries if entry["kind"] == "HERO"}


def _node() -> str | None:
    node = shutil.which("node")
    if node is None:
        return None
    version = subprocess.run([node, "--version"], capture_output=True, text=True, check=True).stdout
    major, minor = (int(part) for part in version.strip().lstrip("v").split(".")[:2])
    # Type stripping runs unflagged from Node 22.18 and 23.6.
    return node if (major, minor) >= (22, 18) and (major, minor) != (23, 0) else None


NODE = _node()
needs_node = pytest.mark.skipif(NODE is None, reason="needs Node 22.18+ to run lib/journeyState.ts")


def probe(**request: object) -> dict:  # type: ignore[type-arg]
    assert NODE is not None
    result = subprocess.run(
        [NODE, str(PROBE)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
        env={**os.environ, "NODE_NO_WARNINGS": "1"},
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


THROUGH = ["S01", "S02", "S03", "S04"]


@pytest.fixture(scope="module")
def journey_run() -> dict:  # type: ignore[type-arg]
    if NODE is None:
        pytest.skip("needs Node 22.18+ to run lib/journeyState.ts")
    return probe(through=[*THROUGH, "S05"], contexts=["S01", "S02", "S03", "S04", "S05", "S30"])


def _by_id(items: list[dict]) -> dict[str, dict]:  # type: ignore[type-arg]
    return {item["id"]: item for item in items}


# ---------------------------------------------------------------------------
# Route and data
# ---------------------------------------------------------------------------


def test_journey_route_exists_with_title_and_canonical() -> None:
    page = _read(PAGE)
    assert 'title: "Journey Map · The Class Expedition | Course4Teen"' in page
    assert "alternates: { canonical: JOURNEY_HREF }" in page
    assert 'export const JOURNEY_HREF = "/students/journey/";' in _read(JOURNEY_LIB)


@needs_node
def test_journey_data_validates_against_calendar_publication_and_manifest(journey_run) -> None:  # type: ignore[no-untyped-def]
    assert journey_run["errors"] == []


def test_exactly_one_detailed_stop_per_published_session() -> None:
    stops = [stop["session"] for stop in _journey()["stops"]]
    assert stops == _published() == ["S01", "S02", "S03", "S04"]
    kinds = {stop["session"]: (stop["kind"], stop["landmark"]) for stop in _journey()["stops"]}
    assert kinds == {
        "S01": ("arrive", "landing-site"),
        "S02": ("reveal", "compass-clearing"),
        "S03": ("deepen", "compass-clearing"),
        "S04": ("reveal", "moonlit-guide"),
    }
    for stop in _journey()["stops"]:
        assert len(stop["story"]) <= 90, stop["session"]


def test_journey_data_duplicates_no_calendar_or_url_facts() -> None:
    text = _read(JOURNEY_JSON)
    for session in _calendar().values():
        assert session["title"] not in text, session["id"]
        assert session["date"] not in text, session["id"]
    for key in ('"title"', '"date"', '"href"', '"url"', '"slides"', '"notes"', '"published"'):
        assert key not in text, key
    assert "/students/" not in text


# ---------------------------------------------------------------------------
# Current stop and progressive reveal
# ---------------------------------------------------------------------------


@needs_node
def test_current_stop_is_s04_on_the_moonlit_ridge(journey_run) -> None:  # type: ignore[no-untyped-def]
    assert journey_run["current"] == "S04"
    state = journey_run["states"]["S04"]
    current = state["currentStop"]
    assert current["session"]["id"] == "S04"
    assert current["place"] == "Moonlit Ridge"
    assert current["location"] == "Moonlit Guide · Moonlit Ridge"
    assert (current["session"]["number"], state["totalSessions"]) == (4, 30)
    assert state["nextSession"] == _calendar()["S05"]


EXPECTED = {
    "S01": {
        "regions": {"moon-meadow": "revealed", "moonlit-ridge": "fogged"},
        "landmarks": {
            "landing-site": "current",
            "lantern-shrine": "revealed",
            "compass-clearing": "hinted",
        },
        "paths": {"trail-landing-clearing": "revealed", "trail-clearing-shrine": "revealed"},
    },
    "S02": {
        "regions": {"moon-meadow": "revealed", "moonlit-ridge": "fogged"},
        "landmarks": {
            "landing-site": "revealed",
            "lantern-shrine": "revealed",
            "compass-clearing": "current",
        },
        "paths": {"trail-landing-clearing": "revealed", "trail-clearing-shrine": "revealed"},
    },
    "S03": {
        "regions": {"moon-meadow": "revealed", "moonlit-ridge": "fogged"},
        "landmarks": {
            "landing-site": "revealed",
            "lantern-shrine": "revealed",
            "compass-clearing": "current",
            "moonlit-guide": "hinted",
        },
        "paths": {
            "trail-landing-clearing": "revealed",
            "trail-clearing-shrine": "revealed",
            "bearing-clearing-guide": "hinted",
        },
    },
    "S04": {
        "regions": {
            "moon-meadow": "revealed",
            "moonlit-ridge": "revealed",
            "beyond-ridge": "fogged",
        },
        "landmarks": {
            "landing-site": "revealed",
            "lantern-shrine": "revealed",
            "compass-clearing": "revealed",
            "moonlit-guide": "current",
        },
        "paths": {
            "trail-landing-clearing": "revealed",
            "trail-clearing-shrine": "revealed",
            "bearing-clearing-guide": "revealed",
        },
    },
}


@needs_node
@pytest.mark.parametrize("through", THROUGH)
def test_reveal_state_through_each_published_session(journey_run, through) -> None:  # type: ignore[no-untyped-def]
    state = journey_run["states"][through]
    for kind in ("regions", "landmarks", "paths"):
        got = {item["id"]: item["state"] for item in state[kind]}
        assert got == EXPECTED[through][kind], (through, kind)
    assert [stop["session"]["id"] for stop in state["stops"]] == THROUGH[
        : THROUGH.index(through) + 1
    ]
    assert state["currentStop"]["session"]["id"] == through
    assert sum(item["state"] == "current" for item in state["landmarks"]) == 1


@needs_node
def test_hinted_things_carry_no_name_and_hidden_things_are_absent(journey_run) -> None:  # type: ignore[no-untyped-def]
    s01 = journey_run["states"]["S01"]
    clearing = _by_id(s01["landmarks"])["compass-clearing"]
    assert clearing["name"] is None and clearing["hint"] == "An empty circle of tall stones"
    assert "moonlit-guide" not in _by_id(s01["landmarks"])
    assert "beyond-ridge" not in _by_id(s01["regions"])
    assert "bearing-clearing-guide" not in _by_id(s01["paths"])
    assert _by_id(s01["regions"])["moonlit-ridge"]["name"] is None
    assert "Compass Clearing" not in json.dumps(s01["landmarks"])

    s02 = _by_id(journey_run["states"]["S02"]["landmarks"])
    assert s02["compass-clearing"]["name"] == "Compass Clearing"
    assert s02["compass-clearing"]["detail"] is None

    s03 = _by_id(journey_run["states"]["S03"]["landmarks"])
    assert s03["compass-clearing"]["detail"] == "awakened"
    assert s03["moonlit-guide"]["name"] is None
    assert s03["moonlit-guide"]["hint"] == "A lantern glow past the trees"
    assert "Moonlit Guide" not in json.dumps(journey_run["states"]["S03"]["landmarks"])

    s04 = journey_run["states"]["S04"]
    assert _by_id(s04["landmarks"])["moonlit-guide"]["name"] == "Moonlit Guide"
    assert _by_id(s04["regions"])["moonlit-ridge"]["name"] == "Moonlit Ridge"


@needs_node
def test_unpublished_session_has_no_journey_state(journey_run) -> None:  # type: ignore[no-untyped-def]
    assert journey_run["states"]["S05"] == {"error": "No published Journey stop for S05"}


def test_only_one_generic_unnamed_fog_frontier() -> None:
    frontiers = [region for region in _journey()["regions"] if region.get("frontier")]
    assert len(frontiers) == 1
    (frontier,) = frontiers
    assert "name" not in frontier
    assert {step["state"] for step in frontier["reveal"]} == {"fogged"}
    assert [step["from"] for step in frontier["reveal"]] == ["S04"]
    # Its only text is the S04 Guide's own published words.
    assert _journey()["frontier"]["teaser"] == "The trail beyond the ridge has gone dark."
    guide = _read(
        ROOT
        / "lessons"
        / "sessions"
        / "s04"
        / "student"
        / "explorer-package"
        / "character"
        / "guide.yaml"
    )
    assert "the trail beyond this ridge has gone dark" in guide


@needs_node
def test_frontier_stays_unnamed_in_state(journey_run) -> None:  # type: ignore[no-untyped-def]
    frontier = _by_id(journey_run["states"]["S04"]["regions"])["beyond-ridge"]
    assert frontier == {**frontier, "name": None, "frontier": True, "state": "fogged"}


# ---------------------------------------------------------------------------
# Future-content boundary
# ---------------------------------------------------------------------------


def test_journey_data_names_no_unpublished_session() -> None:
    named = set(re.findall(r"\bS(\d\d)\b", _read(JOURNEY_JSON)))
    assert {f"S{number}" for number in named} <= set(_published())


@pytest.mark.parametrize("path", JOURNEY_FILES, ids=lambda path: path.name)
def test_journey_files_carry_no_later_story(path: Path) -> None:
    text = _read(path)
    for term in LATER_STORY:
        assert term not in text, f"{path.name} mentions later-session content: {term!r}"


def test_journey_icons_are_only_published_entities() -> None:
    icons = {landmark["icon"] for landmark in _journey()["landmarks"]}
    assert icons == {"lander", "lantern", "compass", "guide"}
    names = {landmark["name"] for landmark in _journey()["landmarks"]}
    assert names == {"Landing Site", "Lantern Shrine", "Compass Clearing", "Moonlit Guide"}
    regions = {region.get("name") for region in _journey()["regions"]}
    assert regions == {"Moon Meadow", "Moonlit Ridge", None}


def test_journey_keeps_no_per_student_progress() -> None:
    for path in JOURNEY_FILES:
        text = _read(path)
        for forbidden in (
            "localStorage",
            "sessionStorage",
            "document.cookie",
            "indexedDB",
            '"use client"',
        ):
            assert forbidden not in text, (path.name, forbidden)


def _mutated(change) -> dict:  # type: ignore[no-untyped-def,type-arg]
    data = copy.deepcopy(_journey())
    change(data)
    return data


def _errors(**request: object) -> list[str]:
    return probe(**request)["errors"]


@needs_node
def test_validation_rejects_a_published_session_without_a_stop() -> None:
    errors = _errors(published=["S01", "S02", "S03", "S04", "S05"])
    assert any("must be exactly the published sessions" in error for error in errors), errors


@needs_node
def test_validation_rejects_detail_for_an_unpublished_session() -> None:
    def future_stop(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"].append({**data["stops"][-1], "session": "S05"})

    def future_landmark(data: dict) -> None:  # type: ignore[type-arg]
        data["landmarks"].append(
            {
                **data["landmarks"][0],
                "id": "future",
                "name": "Future Place",
                "reveal": [{"from": "S05", "state": "revealed"}],
            }
        )

    def named_but_only_hinted(data: dict) -> None:  # type: ignore[type-arg]
        data["landmarks"].append(
            {
                **data["landmarks"][2],
                "id": "teaser",
                "name": "Teaser",
                "reveal": [{"from": "S04", "state": "hinted"}],
            }
        )

    assert any(
        "must be exactly the published sessions" in e
        for e in _errors(journey=_mutated(future_stop))
    )
    assert any("no published Journey stop" in e for e in _errors(journey=_mutated(future_landmark)))
    assert any("never revealed" in e for e in _errors(journey=_mutated(named_but_only_hinted)))


@needs_node
def test_validation_rejects_missing_or_non_hero_snapshots() -> None:
    def missing(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][3]["snapshot"] = "S04_MISSING"

    def not_hero(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][1]["snapshot"] = "S02_MOVED_COMPASS"

    assert any("does not publish" in e for e in _errors(journey=_mutated(missing)))
    assert any("must be that session's HERO" in e for e in _errors(journey=_mutated(not_hero)))


@needs_node
def test_validation_rejects_duplicated_titles_dates_and_extra_frontiers() -> None:
    def title(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][0]["title"] = "Explorer's Field Notes"

    def second_frontier(data: dict) -> None:  # type: ignore[type-arg]
        data["regions"].append({**data["regions"][2], "id": "beyond-two"})

    def long_story(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][0]["story"] = "x" * 91

    assert any("unknown key title" in e for e in _errors(journey=_mutated(title)))
    assert any("one generic fog frontier" in e for e in _errors(journey=_mutated(second_frontier)))
    assert any("over 90 characters" in e for e in _errors(journey=_mutated(long_story)))


# ---------------------------------------------------------------------------
# Frontier: exactly one generic fog bank, failing closed
# ---------------------------------------------------------------------------


def _frontier_index(data: dict) -> int:  # type: ignore[type-arg]
    (index,) = [i for i, region in enumerate(data["regions"]) if region.get("frontier")]
    return index


def _no_frontier(data: dict) -> None:  # type: ignore[type-arg]
    del data["regions"][_frontier_index(data)]


def _two_frontiers(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"].append({**data["regions"][_frontier_index(data)], "id": "beyond-two"})


def _same_frontier_twice(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"].append(copy.deepcopy(data["regions"][_frontier_index(data)]))


def _named_frontier(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"][_frontier_index(data)]["name"] = "Far Ridge"


def _empty_named_frontier(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"][_frontier_index(data)]["name"] = ""


def _frontier_too_early(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"][_frontier_index(data)]["reveal"] = [{"from": "S03", "state": "fogged"}]


def _frontier_revealed(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"][_frontier_index(data)]["reveal"].append({"from": "S04", "state": "revealed"})


def _frontier_detail(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"][_frontier_index(data)]["reveal"][0]["detail"] = "a tower"


def _frontier_hint_field(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"][_frontier_index(data)]["hint"] = "A tower glows beyond the ridge"


def _frontier_object_field(data: dict) -> None:  # type: ignore[type-arg]
    data["frontier"]["destination"] = "A tower beyond the ridge"


def _frontier_future_teaser(data: dict) -> None:  # type: ignore[type-arg]
    data["frontier"]["teaser"] = "A tower of stars waits beyond the ridge."


def _frontier_empty_teaser(data: dict) -> None:  # type: ignore[type-arg]
    data["frontier"]["teaser"] = " "


def _frontier_flag_not_true(data: dict) -> None:  # type: ignore[type-arg]
    data["regions"][_frontier_index(data)]["frontier"] = "yes"


def _landmark_in_frontier(data: dict) -> None:  # type: ignore[type-arg]
    data["landmarks"][3]["region"] = data["regions"][_frontier_index(data)]["id"]


FRONTIER_MUTATIONS = {
    "zero": (_no_frontier, "exactly one generic fog frontier is required; found 0"),
    "two": (_two_frontiers, "exactly one generic fog frontier is required; found 2"),
    "duplicate": (_same_frontier_twice, "exactly one generic fog frontier is required; found 2"),
    "named": (_named_frontier, "must stay unnamed"),
    "empty-name": (_empty_named_frontier, "must stay unnamed"),
    "too-early": (_frontier_too_early, "must appear once, fogged, at the current stop S04"),
    "revealed": (_frontier_revealed, "must appear once, fogged, at the current stop S04"),
    "detail": (_frontier_detail, "may carry no reveal detail"),
    "hint-field": (_frontier_hint_field, "has unknown key hint"),
    "object-field": (_frontier_object_field, "journey.frontier has unknown key destination"),
    "future-teaser": (_frontier_future_teaser, "teaser must only echo the current stop's published story"),
    "empty-teaser": (_frontier_empty_teaser, "teaser must only echo the current stop's published story"),
    "flag-not-true": (_frontier_flag_not_true, "frontier must be true when present"),
    "holds-landmark": (_landmark_in_frontier, "cannot sit in the unnamed frontier"),
}


@needs_node
@pytest.mark.parametrize("case", sorted(FRONTIER_MUTATIONS))
def test_validation_fails_closed_on_frontier_mutations(case: str) -> None:
    change, message = FRONTIER_MUTATIONS[case]
    errors = _errors(journey=_mutated(change))
    assert any(message in error for error in errors), errors


@needs_node
def test_frontier_is_visible_only_at_the_current_published_stop(journey_run) -> None:  # type: ignore[no-untyped-def]
    for through in THROUGH:
        frontiers = [r for r in journey_run["states"][through]["regions"] if r["frontier"]]
        if through == "S04":
            assert [(r["id"], r["name"], r["state"]) for r in frontiers] == [
                ("beyond-ridge", None, "fogged")
            ]
        else:
            assert frontiers == [], through


# ---------------------------------------------------------------------------
# Path endpoints exist, at an allowed visibility, whenever the line is shown
# ---------------------------------------------------------------------------


def _path(data: dict, path_id: str) -> dict:  # type: ignore[type-arg]
    (path,) = [path for path in data["paths"] if path["id"] == path_id]
    return path


def _landmark(data: dict, landmark_id: str) -> dict:  # type: ignore[type-arg]
    (landmark,) = [item for item in data["landmarks"] if item["id"] == landmark_id]
    return landmark


def _typo_endpoint(data: dict) -> None:  # type: ignore[type-arg]
    _path(data, "trail-landing-clearing")["to"] = "compass-clearng"


def _future_endpoint(data: dict) -> None:  # type: ignore[type-arg]
    data["landmarks"].append(
        {**_landmark(data, "landing-site"), "id": "far-camp", "name": "Far Camp",
         "reveal": [{"from": "S05", "state": "revealed"}]}
    )
    _path(data, "bearing-clearing-guide")["to"] = "far-camp"


def _hidden_endpoint(data: dict) -> None:  # type: ignore[type-arg]
    # The Guide is no longer hinted in S03, yet the S03 bearing still points at it.
    _landmark(data, "moonlit-guide")["reveal"] = [{"from": "S04", "state": "revealed"}]


def _line_before_endpoint(data: dict) -> None:  # type: ignore[type-arg]
    _path(data, "bearing-clearing-guide")["reveal"][0]["from"] = "S02"


def _revealed_bearing_to_hint(data: dict) -> None:  # type: ignore[type-arg]
    _path(data, "bearing-clearing-guide")["reveal"] = [{"from": "S03", "state": "revealed"}]


def _line_between_hints(data: dict) -> None:  # type: ignore[type-arg]
    data["paths"].append(
        {**_path(data, "trail-landing-clearing"), "id": "trail-unanchored",
         "from": "compass-clearing", "to": "moonlit-guide",
         "reveal": [{"from": "S01", "state": "hinted"}, {"from": "S04", "state": "revealed"}]}
    )
    _landmark(data, "moonlit-guide")["reveal"] = [
        {"from": "S01", "state": "hinted"}, {"from": "S04", "state": "revealed"}
    ]


PATH_MUTATIONS = {
    "unknown-endpoint": (_typo_endpoint, "path trail-landing-clearing names unknown landmark compass-clearng"),
    "future-endpoint": (_future_endpoint, "its end far-camp is hidden there"),
    "hidden-endpoint": (_hidden_endpoint, "bearing-clearing-guide is hinted in S03, but its end moonlit-guide is hidden there"),
    "line-before-endpoint": (_line_before_endpoint, "bearing-clearing-guide is hinted in S02, but its end moonlit-guide is hidden there"),
    "revealed-bearing-to-hint": (_revealed_bearing_to_hint, "bearing bearing-clearing-guide is revealed in S03, but its end moonlit-guide is only hinted"),
    "unanchored-line": (_line_between_hints, "trail-unanchored is hinted in S01, but neither end is revealed there"),
}


@needs_node
@pytest.mark.parametrize("case", sorted(PATH_MUTATIONS))
def test_validation_fails_closed_on_path_endpoint_mutations(case: str) -> None:
    change, message = PATH_MUTATIONS[case]
    errors = _errors(journey=_mutated(change))
    assert any(message in error for error in errors), errors


@needs_node
@pytest.mark.parametrize("through", THROUGH)
def test_every_shown_path_ends_at_landmarks_shown_in_the_same_state(journey_run, through) -> None:  # type: ignore[no-untyped-def]
    state = journey_run["states"][through]
    landmarks = {item["id"]: item["state"] for item in state["landmarks"]}
    for path in state["paths"]:
        ends = [landmarks.get(path["from"]), landmarks.get(path["to"])]
        assert all(end in {"hinted", "revealed", "current"} for end in ends), (through, path["id"], ends)
        assert any(end in {"revealed", "current"} for end in ends), (through, path["id"], ends)
        if path["kind"] == "bearing" and path["state"] == "revealed":
            assert all(end in {"revealed", "current"} for end in ends), (through, path["id"], ends)


# ---------------------------------------------------------------------------
# Canonical fields are derived, never owned: rejected at any depth
# ---------------------------------------------------------------------------


def _nest(where, key: str, value: object):  # type: ignore[no-untyped-def]
    def change(data: dict) -> None:  # type: ignore[type-arg]
        where(data)["meta"] = {key: value}

    return change


NESTED_HOSTS = {
    "stop": lambda data: data["stops"][0],
    "landmark": lambda data: data["landmarks"][2],
    "region": lambda data: data["regions"][1],
    "reveal-step": lambda data: data["landmarks"][2]["reveal"][1],
    "frontier-object": lambda data: data["frontier"],
    "frontier-region": lambda data: data["regions"][_frontier_index(data)],
    "path": lambda data: data["paths"][2],
    "map": lambda data: data["map"],
    "label": lambda data: data["regions"][0]["label"],
}

NESTED_FIELDS = {
    "title": "Place Your First Prop",
    "date": "2026-09-26",
    "published": True,
    "publicationState": "published",
    "slidesUrl": "/students/slides/s02/",
    "notesHref": "/students/learn/s02/",
    "learnUrl": "/students/learn/s02/",
    "heroSrc": "/journey/s02/hero.webp",
    "snapshot": "S02_COMPASS_PROMPT",
}


@needs_node
@pytest.mark.parametrize("host", sorted(NESTED_HOSTS))
@pytest.mark.parametrize("field", sorted(NESTED_FIELDS))
def test_validation_rejects_nested_canonical_fields(host: str, field: str) -> None:
    errors = _errors(journey=_mutated(_nest(NESTED_HOSTS[host], field, NESTED_FIELDS[field])))
    assert any(f"has canonical field {field}, which journey.json must not own" in e for e in errors), errors


@needs_node
def test_validation_rejects_canonical_fields_buried_deeper_or_in_scalars() -> None:
    def deep(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][1]["extra"] = {"layers": [{"session": {"title": "Place Your First Prop"}}]}

    def direct(data: dict) -> None:  # type: ignore[type-arg]
        data["paths"][0]["url"] = "/students/slides/s01/"

    def in_scalar(data: dict) -> None:  # type: ignore[type-arg]
        data["landmarks"][0]["icon"] = {"image": {"src": "/journey/s01/hero.webp"}}

    def image_list(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][0]["images"] = [{"src": "/journey/s01/hero-480.webp"}]

    assert any(
        "journey.stops[1].extra.layers[0].session has canonical field title" in e
        for e in _errors(journey=_mutated(deep))
    )
    assert any("journey.paths[0] has canonical field url" in e for e in _errors(journey=_mutated(direct)))
    errors = _errors(journey=_mutated(in_scalar))
    assert any("journey.landmarks[0].icon must be a string" in e for e in errors), errors
    assert any("icon has canonical field image" in e for e in errors), errors
    assert any("has canonical field src" in e for e in errors), errors
    errors = _errors(journey=_mutated(image_list))
    assert any("journey.stops[0] has canonical field images" in e for e in errors), errors


@needs_node
def test_validation_rejects_canonical_values_inside_owned_text() -> None:
    def dated(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][0]["story"] = "On 2026-09-19 Nova lands in Moon Meadow."

    def titled(data: dict) -> None:  # type: ignore[type-arg]
        data["landmarks"][0]["hint"] = "Explorer's Field Notes"

    def linked(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][2]["snapshotAlt"] = "See /journey/s03/hero.webp"

    def slides_link(data: dict) -> None:  # type: ignore[type-arg]
        data["note"] = "Slides live at https://example.org/s01"

    assert any("carries a date" in e for e in _errors(journey=_mutated(dated)))
    assert any("repeats the calendar title of S01" in e for e in _errors(journey=_mutated(titled)))
    assert any("carries a URL or image path" in e for e in _errors(journey=_mutated(linked)))
    assert any("carries a URL or image path" in e for e in _errors(journey=_mutated(slides_link)))


@needs_node
def test_descriptive_prose_with_ordinary_words_still_validates() -> None:
    def prose(data: dict) -> None:  # type: ignore[type-arg]
        data["stops"][0]["story"] = "Nova notes the date and a title on the slides of a published map."

    assert _errors(journey=_mutated(prose)) == []


# ---------------------------------------------------------------------------
# SVG ids are scoped per map instance
# ---------------------------------------------------------------------------

SVG_ID = re.compile(r'\sid="([^"]+)"')
SVG_REFS = (
    re.compile(r'url\(#([^)"\']+)\)'),
    re.compile(r'(?:xlink:)?href="#([^"]+)"'),
)


def _svg_refs(svg: str) -> set[str]:
    refs = {ref for pattern in SVG_REFS for ref in pattern.findall(svg)}
    for labels in re.findall(r'aria-labelledby="([^"]+)"', svg):
        refs.update(labels.split())
    return refs


def _check_svg_instances(html: str, count: int) -> None:
    svgs = re.findall(r"<svg\b.*?</svg>", html, flags=re.S)
    assert len(svgs) == count
    all_ids = SVG_ID.findall(html)
    assert len(all_ids) == len(set(all_ids)), sorted(i for i in all_ids if all_ids.count(i) > 1)
    owned = [set(SVG_ID.findall(svg)) for svg in svgs]
    for index, svg in enumerate(svgs):
        refs = _svg_refs(svg)
        assert refs, index
        # Every local reference resolves inside its own map, never a sibling's.
        assert refs <= owned[index], (index, refs - owned[index])
        for other, ids in enumerate(owned):
            if other != index:
                assert not refs & ids, (index, other)


SAFE_SVG_ID = re.compile(r"[A-Za-z0-9_-]+")
needs_react = pytest.mark.skipif(
    not (WEBSITE / "node_modules" / "react-dom").is_dir(),
    reason="needs the website's node_modules (npm ci) to server-render JourneyMap",
)


def _render_maps(*id_prefixes: str | None, identifier_prefix: str | None = None) -> str:
    entries = [{"through": "S04"} if prefix is None else {"through": "S04", "idPrefix": prefix} for prefix in id_prefixes]
    request: dict[str, object] = {"render": entries}
    if identifier_prefix is not None:
        request["identifierPrefix"] = identifier_prefix
    rendered = probe(**request)["rendered"]
    assert rendered.startswith("<main")
    _check_svg_instances(rendered, len(id_prefixes))
    for svg_id in SVG_ID.findall(rendered):
        assert SAFE_SVG_ID.fullmatch(svg_id), svg_id
    return rendered


@needs_node
@needs_react
def test_two_map_instances_in_one_document_never_share_svg_ids() -> None:
    rendered = probe(render=[{"through": "S04"}, {"through": "S04"}, {"through": "S01"}])["rendered"]
    assert rendered.startswith("<main>")
    _check_svg_instances(rendered, 3)
    for paint in ("sky", "meadow", "vignette", "blur", "soft", "frame"):
        assert len(re.findall(rf'id="[^"]+-{paint}"', rendered)) == 3, paint


@needs_node
@needs_react
def test_default_instances_get_distinct_namespaces() -> None:
    rendered = _render_maps(None, None)
    skies = re.findall(r'id="(jm-[A-Za-z0-9_]+)-sky"', rendered)
    assert len(skies) == 2 and skies[0] != skies[1], skies


@needs_node
@needs_react
def test_identical_id_prefixes_still_get_distinct_namespaces() -> None:
    rendered = _render_maps("same", "same", "same")
    skies = re.findall(r'id="(same-[A-Za-z0-9_]+)-sky"', rendered)
    assert len(set(skies)) == 3, skies


@needs_node
@needs_react
def test_sanitization_equivalent_id_prefixes_still_get_distinct_namespaces() -> None:
    rendered = _render_maps("map:b", "mapb", "m a p b")
    skies = re.findall(r'id="(mapb-[A-Za-z0-9_]+)-sky"', rendered)
    assert len(set(skies)) == 3, skies


@needs_node
@needs_react
def test_empty_id_prefixes_fall_back_to_a_unique_namespace() -> None:
    # "" and a prefix that sanitizes to nothing both fall back to "jm", beside a default map.
    rendered = _render_maps("", ":::", None)
    skies = re.findall(r'id="(jm-[A-Za-z0-9_]+)-sky"', rendered)
    assert len(set(skies)) == 3, skies


@needs_node
@needs_react
def test_unusual_punctuation_prefixes_give_safe_unique_ids() -> None:
    rendered = _render_maps("  <x\"y'>#(z) é-1 ", 'url(#a)"', "x\"y'z(1)", "-_-")
    assert 'id="xyz-1-' in rendered and 'id="urla-' in rendered and 'id="xyz1-' in rendered
    assert 'id="-_--' in rendered


@needs_node
@needs_react
def test_react_ids_with_unusual_characters_stay_safe_and_unique() -> None:
    # useId carries React's identifierPrefix, so its characters are encoded, not dropped.
    _render_maps("same", "same", None, identifier_prefix="a:b-«c» d")


@needs_node
@needs_react
def test_explicit_id_prefix_stays_visible_in_ids() -> None:
    rendered = _render_maps("map-a")
    ids = SVG_ID.findall(rendered)
    assert ids and all(svg_id.startswith("map-a-") for svg_id in ids), ids
    assert re.search(r'id="map-a-[A-Za-z0-9_]+-sky"', rendered)


@needs_node
def test_svg_id_namespace_is_injective_over_instances() -> None:
    # Distinct useIds never share a namespace, whatever hints the callers pass,
    # including ids that only differ in characters a strip would drop.
    instances = ["_R_1_", "_R_2_", "R1", ":R1:", "«R1»", "R:1", "R_1", "_52_1", "a-b", "ab", "a_2d_b", ""]
    hints = [None, "", ":::", "jm", "same", "map:b", "mapb", "x-y", "x", "-", "_"]
    pairs = [[instance, hint] for instance in instances for hint in hints]
    namespaces = probe(namespaces=pairs)["namespaces"]
    by_namespace: dict[str, set[str]] = {}
    for (instance, _), namespace in zip(pairs, namespaces):
        assert SAFE_SVG_ID.fullmatch(namespace), namespace
        by_namespace.setdefault(namespace, set()).add(instance)
    assert all(len(owners) == 1 for owners in by_namespace.values()), by_namespace
    assert namespaces[pairs.index(["_R_1_", "same"])] == "same-_5f_R_5f_1_5f_"
    assert namespaces[pairs.index(["_R_1_", None])].startswith("jm-")


def test_map_ids_come_from_a_server_safe_per_instance_source() -> None:
    journey_map = _read(MAP)
    assert 'import { useId } from "react";' in journey_map
    assert '"use client"' not in journey_map
    assert 'idPrefix = "jm"' not in journey_map
    # The useId part is always in the namespace; idPrefix is only a hint.
    assert "const prefix = svgIdNamespace(useId(), idPrefix);" in journey_map
    assert "return `${hint}-${instance}`;" in journey_map
    # The component body reads idPrefix exactly once, and only to pass it as the hint.
    body = journey_map[journey_map.index("export default function JourneyMap") :]
    assert body.count("idPrefix") == 2, body.count("idPrefix")
    for nondeterministic in ("Math.random", "Date.now", "new Date", "crypto", "performance.now"):
        assert nondeterministic not in journey_map, nondeterministic
    # No hard-coded paint ids: every id and url(#...) goes through `ids`.
    assert not re.search(r'id="[^"]*"', journey_map)
    assert not re.search(r"url\(#[a-z]", journey_map)


# ---------------------------------------------------------------------------
# Snapshots, links, and canonical metadata
# ---------------------------------------------------------------------------


@needs_node
def test_every_stop_shows_its_manifest_hero(journey_run) -> None:  # type: ignore[no-untyped-def]
    heroes = _heroes()
    for stop in journey_run["states"]["S04"]["stops"]:
        sid = stop["session"]["id"]
        entry = heroes[sid]
        assert stop["hero"]["full"] == {
            k: entry["images"]["960"][k] for k in ("src", "width", "height")
        }
        assert stop["hero"]["small"] == {
            k: entry["images"]["480"][k] for k in ("src", "width", "height")
        }
        assert stop["hero"]["full"]["src"] == f"/journey/{sid.lower()}/hero.webp"
        for image in stop["hero"].values():
            if isinstance(image, dict):
                assert (WEBSITE / "public" / image["src"].lstrip("/")).is_file()
        assert stop["hero"]["alt"].startswith(f"The Trail in {sid}:")


@needs_node
def test_stop_links_reach_real_slides_and_notes(journey_run) -> None:  # type: ignore[no-untyped-def]
    for stop in journey_run["states"]["S04"]["stops"]:
        slug = stop["session"]["id"].lower()
        assert stop["slidesHref"] == f"/students/slides/{slug}/"
        assert (WEBSITE / "app" / "students" / "slides" / slug / "page.tsx").is_file()
        assert stop["notesHref"] == f"/students/learn/{slug}/"
        assert stop["session"]["id"] in _learn_ids()


@needs_node
def test_stop_titles_and_dates_come_from_the_calendar(journey_run) -> None:  # type: ignore[no-untyped-def]
    calendar = _calendar()
    for stop in journey_run["states"]["S04"]["stops"]:
        assert stop["session"] == calendar[stop["session"]["id"]]


# ---------------------------------------------------------------------------
# JourneyContext on Slides and Python Notes
# ---------------------------------------------------------------------------

CONTEXTS = {
    "S01": ("Landing Site · Moon Meadow", "Nova lands in Moon Meadow"),
    "S02": ("Compass Clearing · Moon Meadow", "first instrument"),
    "S03": ("Compass Clearing · Moon Meadow", "The Moon Compass reacts and points past the trees"),
    "S04": ("Moonlit Guide · Moonlit Ridge", "the trail beyond the ridge has gone dark"),
}


@needs_node
@pytest.mark.parametrize("session", sorted(CONTEXTS))
def test_journey_context_for_each_published_session(journey_run, session) -> None:  # type: ignore[no-untyped-def]
    view = journey_run["contexts"][session]
    location, story = CONTEXTS[session]
    assert view["location"] == location
    assert story in view["story"]
    assert view["session"]["number"] == int(session[1:])


@needs_node
def test_unpublished_sessions_get_no_journey_context(journey_run) -> None:  # type: ignore[no-untyped-def]
    assert journey_run["contexts"]["S05"] is None
    assert journey_run["contexts"]["S30"] is None
    assert "if (!stop) return null;" in _read(CONTEXT)


@pytest.mark.parametrize("session", sorted(CONTEXTS))
def test_journey_context_sits_in_the_slides_hero_not_a_slide(session: str) -> None:
    page = _read(WEBSITE / "app" / "students" / "slides" / session.lower() / "page.tsx")
    assert 'import JourneyContext from "../../../components/JourneyContext";' in page
    hero = page.split('className="section slides-hero"', 1)[1].split(
        'className="section slide-deck"', 1
    )[0]
    assert "<JourneyContext session={session.id} />" in hero
    assert page.count("<JourneyContext") == 1


def test_journey_context_sits_in_the_learn_page_hero() -> None:
    page = _read(LEARN_PAGE)
    hero = page.split('className="section slides-hero"', 1)[1].split(
        'className="section slide-deck"', 1
    )[0]
    assert "<JourneyContext session={session.id} />" in hero
    assert page.count("<JourneyContext") == 1


# ---------------------------------------------------------------------------
# Slides index, home, and page accessibility
# ---------------------------------------------------------------------------


def test_slides_index_links_the_journey_and_shows_locations() -> None:
    index = _read(SLIDES_INDEX)
    assert 'import { JOURNEY_HREF, journeyContext } from "../../../lib/journey";' in index
    assert "href={JOURNEY_HREF}" in index
    assert "Journey Map" in index
    assert "const stop = isPublished ? journeyContext(session.id) : null;" in index
    assert "{stop.location}" in index


def test_home_links_the_journey_once() -> None:
    home = _read(HOME)
    assert home.count("href={JOURNEY_HREF}") == 1
    assert "<JourneyMap" not in home


def test_map_has_a_text_equivalent_and_no_hover_only_information() -> None:
    page = _read(PAGE)
    journey_map = _read(MAP)
    assert 'role="img"' in journey_map
    assert "aria-labelledby={`${ids.title} ${ids.desc}`}" in journey_map
    assert "<desc" in journey_map and "<title" in journey_map
    assert 'className="journey-key-list"' in page
    assert 'className="journey-stop-list"' in page
    assert "Current stop" in page
    for hover_only in ("onMouseEnter", "onMouseOver", ":hover", "title={"):
        assert hover_only not in journey_map, hover_only


def test_map_animation_respects_reduced_motion() -> None:
    css = _read(CSS)
    reduced = css.split("@media (prefers-reduced-motion: reduce)", 1)[1]
    assert ".jm-drift, .jm-gem { animation: none; }" in reduced
    animated = set(re.findall(r"\.(jm-[a-z-]+) \{ animation:", css))
    assert animated == {"jm-drift", "jm-gem"}


def test_journey_page_wording_is_about_the_class_not_one_student() -> None:
    page = _read(PAGE)
    assert "not any one student" in page
    assert "sessions taught" in page
    for gamified in ("badge", "points", "XP", "level up", "streak"):
        assert gamified not in page, gamified


# ---------------------------------------------------------------------------
# Rendered HTML (opt in: JOURNEY_SITE_OUT=course4teen-website/out after next build)
# ---------------------------------------------------------------------------

SITE_OUT = os.environ.get("JOURNEY_SITE_OUT")
needs_site = pytest.mark.skipif(
    not SITE_OUT, reason="set JOURNEY_SITE_OUT to a fresh next build output"
)


def _html(route: str) -> str:
    assert SITE_OUT
    return (ROOT / SITE_OUT / route / "index.html").read_text(encoding="utf-8")


def _visible(html: str) -> str:
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    text = unescape(re.sub(r"<[^>]+>", " ", html))
    return re.sub(r"\s+", " ", text)


@needs_site
def test_rendered_journey_page_shows_s04_and_nothing_later() -> None:
    html = _html("students/journey")
    text = _visible(html)
    assert "S04 · Moonlit Ridge" in text
    assert re.search(r"4\s*/\s*30", text)
    for sid in ("s01", "s02", "s03", "s04"):
        assert f"/journey/{sid}/hero-480.webp" in html
        assert f'href="/students/slides/{sid}/"' in html
        assert f'href="/students/learn/{sid}/"' in html
    assert "/journey/s05" not in html
    assert "/students/slides/s05/" not in html
    calendar = _calendar()
    future_titles = {
        session["title"] for sid, session in calendar.items() if sid not in _published()
    }
    for term in LATER_STORY:
        if term in {"Script a Conversation", "conversation"}:
            continue  # S05's public calendar title is listed as coming soon.
        if any(term in title for title in future_titles):
            continue
        assert term not in text, term


@needs_site
def test_rendered_journey_page_svg_ids_are_unique_and_resolve() -> None:
    _check_svg_instances(_html("students/journey"), 1)


@needs_site
def test_rendered_pages_link_the_journey() -> None:
    assert 'href="/students/journey/"' in _html("")
    assert 'href="/students/journey/"' in _html("students/slides")
    for sid in ("s01", "s02", "s03", "s04"):
        for route in (f"students/slides/{sid}", f"students/learn/{sid}"):
            html = _html(route)
            assert 'class="journey-context"' in html, route
            assert 'href="/students/journey/"' in html, route
