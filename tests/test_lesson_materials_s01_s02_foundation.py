"""S01/S02 foundation: course identity, Nova + Pixel, Python Notes, and Discovery."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from engine.entities import Bounds
from engine.input import DirectionalInput, InteractionInput
from explore.curriculum import MISSION_01_ID, MISSION_02_ID
from explore.packages import (
    create_classroom_trail_scene,
    load_explorer_package,
    plan_local_classroom_trail,
)

PROJECT_ROOT = Path(__file__).parents[1]
SESSIONS = PROJECT_ROOT / "lessons" / "sessions"
EXAMPLES = PROJECT_ROOT / "examples" / "explorer-packages"
WEBSITE = PROJECT_ROOT / "course4teen-website"
PIXEL_ROOT = EXAMPLES / "pixel-companion"
STUDENT_MOON_COMPASS = "../my-explore-world/projects/moon-compass"

PYTHON_NOTES_SECTIONS = (
    "## 1. Python concept",
    "## 2. Code we wrote",
    "## 3. What the code means",
    "## 4. Why programmers use this",
    "## 5. What we debugged",
    "## 6. Key Python words",
    "## 7. Try it yourself",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def _trail_packages(task_card: str) -> list[str]:
    command = task_card.split("explore-package trail", 1)[1].split("--player", 1)[0]
    return re.findall(
        r"(?:examples/explorer-packages|lessons/sessions)/[\w/-]+"
        r"|\.\./my-explore-world/projects/[\w/-]+",
        command,
    )


def _source_package_path(package: str) -> Path:
    if package == STUDENT_MOON_COMPASS:
        return SESSIONS / "s02" / "student" / "explorer-package"
    return PROJECT_ROOT / package


# --- S01: course identity without teaching S02 early -------------------------------------


def test_s01_slide_one_establishes_course_identity_nova_and_pixel():
    slides = _read(WEBSITE / "app" / "students" / "slides" / "s01" / "page.tsx")
    first_slide = slides.split("const slides: Slide[] = [", 1)[1].split("kicker:", 2)[1]

    assert "Explore Studio" in first_slide
    assert "Learn Python. Explore Worlds. Build Your Own." in first_slide
    assert "Meet Nova and Pixel" in first_slide
    assert "explorer, companion, and interactive world" in " ".join(first_slide.split())
    assert 'print("Hello, world!")' in first_slide


def test_s01_slide_one_does_not_teach_variables_early():
    slides = _read(WEBSITE / "app" / "students" / "slides" / "s01" / "page.tsx")
    first_slide = slides.split("const slides: Slide[] = [", 1)[1].split("kicker:", 2)[1]

    assert "variable" not in first_slide.lower()
    assert not re.search(r"\b\w+ = [\"\d]", first_slide)


def test_s01_materials_keep_print_and_strings_scope():
    starter = _read(SESSIONS / "s01" / "student" / "starter.py")
    notes = _read(SESSIONS / "s01" / "student" / "python-notes.md")

    assert "=" not in starter
    assert "variable" not in notes.lower()
    assert all(term in notes for term in ("print", "string", "SyntaxError", "quotation marks"))


def test_s01_task_card_distinguishes_explorer_companion_and_world_object():
    task_card = _normalized(SESSIONS / "s01" / "student" / "task-card.md")

    assert "reference explorer is **Nova**" in task_card
    assert "Nova's companion, **Pixel**" in task_card
    assert "**Crystal Lantern** and **River Fountain** are world objects" in task_card
    assert "Moon Compass" not in task_card


def test_s01_sets_the_explorer_and_companion_homework_s02_opens_from():
    task_card = _normalized(SESSIONS / "s01" / "student" / "task-card.md")

    assert "Before Session 2: imagine your explorer and companion" in task_card
    assert "one thing you eventually want your companion to be able to do" in task_card


def test_s01_trail_and_m01_semantics_are_unchanged():
    task_card = _read(SESSIONS / "s01" / "student" / "task-card.md")

    assert _trail_packages(task_card) == [
        "examples/explorer-packages/nova-character",
        "examples/explorer-packages/forest-guide",
        "examples/explorer-packages/crystal-lantern",
        "examples/explorer-packages/river-fountain",
    ]
    assert f'--mission-id "{MISSION_01_ID}"' in task_card
    assert not (SESSIONS / "s01" / "student" / "discovery.md").exists()


# --- Reference cast and engine honesty ---------------------------------------------------


def test_pixel_is_a_valid_static_companion_character_package():
    loaded = load_explorer_package(PIXEL_ROOT)

    assert loaded.is_loaded, loaded.all_issues
    assert loaded.package is not None
    assert [c.name for c in loaded.package.characters] == ["Pixel"]
    assert loaded.package.world_objects == ()
    document = yaml.safe_load(_read(PIXEL_ROOT / "character" / "pixel.yaml"))
    assert set(document) == {"name", "x", "y", "color", "greeting"}


def test_course_identity_keeps_the_four_categories_explicit():
    identity = _normalized(PROJECT_ROOT / "docs" / "course-identity.md")

    assert "| Explorer | **Nova** |" in identity
    assert "| Companion | **Pixel** |" in identity
    assert "| Tool | **Moon Compass** | An exploration instrument. Never a companion. |" in identity
    assert "| World object | **Crystal Lantern** |" in identity
    assert "Pixel **does not** follow Nova" in identity


def test_s02_classifies_moon_compass_as_tool_and_pixel_as_companion():
    task_card = _read(SESSIONS / "s02" / "student" / "task-card.md")

    assert re.search(r"^\| Explorer \| Nova \|", task_card, re.MULTILINE)
    assert re.search(r"^\| Companion \| Pixel \|", task_card, re.MULTILINE)
    assert re.search(r"^\| Tool \| Moon Compass \|", task_card, re.MULTILINE)
    assert re.search(r"^\| World object \| Crystal Lantern \|", task_card, re.MULTILINE)
    assert "companion" not in task_card.split("| Tool | Moon Compass |", 1)[1].split("\n", 1)[0]


def test_s02_is_honest_about_pixel_runtime_behavior():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")
    runbook = _normalized(SESSIONS / "s02" / "teacher-runbook.md")

    assert "it does not follow Nova or make its own decisions yet" in task_card
    assert "Your companion cannot do that yet" in task_card
    assert "It cannot do all of that yet. As you learn more Python, you'll teach it how." in (
        runbook
    )
    assert "It does not follow Nova, remember anything between sessions" in runbook
    for claim in ("Pixel follows", "Pixel remembers", "Pixel decides", "Pixel carries"):
        assert claim not in task_card and claim not in runbook


# --- S02: Python first --------------------------------------------------------------------


def test_s02_teaches_variables_assignment_strings_integers_and_type_contrast():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")

    assert "## Python first: variables and values" in _read(
        SESSIONS / "s02" / "student" / "task-card.md"
    )
    assert "store the integer value `240` under the variable name `x`" in task_card
    assert "**assignment**" in task_card
    assert "**strings**" in task_card and "**integers**" in task_card
    assert '`x = "240"` would store text, not a number' in task_card


def test_s02_opens_with_share_out_then_categories_then_python():
    task_card = _read(SESSIONS / "s02" / "student" / "task-card.md")
    order = [
        task_card.index("## Who will explore your world?"),
        task_card.index("## Explorer, companion, tool, world object"),
        task_card.index("## Python first: variables and values"),
        task_card.index("## Core path"),
    ]
    assert order == sorted(order)


def test_s02_runbook_fits_45_minutes_and_protects_python():
    runbook = _read(SESSIONS / "s02" / "teacher-runbook.md")

    for anchor in (
        "0:00–0:04",
        "0:04–0:15",
        "0:15–0:18",
        "0:18–0:27",
        "0:27–0:35",
        "0:35–0:40",
        "0:40–0:43",
        "0:43–0:45",
    ):
        assert f"| {anchor} |" in runbook
    normalized = " ".join(runbook.split())
    assert "Protected Python teaching" in runbook
    assert "Hard-boxed bootstrap" in runbook
    assert "Bootstrap stops at 0:18" in normalized
    assert "continues the Python lesson" in normalized
    assert "Discovery first" in normalized
    assert "extra discussion" in normalized
    assert "never the core Python explanation/practice" in normalized


def test_s02_requires_complete_concrete_student_ownership_choices():
    task_card = _read(SESSIONS / "s02" / "student" / "task-card.md")
    normalized = " ".join(task_card.split())

    for field in (
        "explorer_name",
        "looks_like",
        "favorite_subject",
        "companion_name",
        "companion_kind",
        "specialty",
        "future_ability",
    ):
        assert f"`{field}`" in task_card
    assert "Replace **every** `TODO` string with concrete choices" in normalized
    assert "do not leave Nova or Pixel as your answers" in normalized
    assert "only a plan written as text" in normalized


def test_s02_exit_check_covers_python_ownership_and_discovery():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")
    exit_check = task_card.split("## Exit check", 1)[1].split("## Looking ahead", 1)[0]

    for question in (
        "What is a variable?",
        "Which values today were strings?",
        "What does changing `x` do?",
        "Explorer's name, appearance, personality",
        "interest or favorite subject",
        "Companion's name, kind, personality",
        "specialty or interest",
        "future ability",
        "What do coordinates describe?",
        "real magnetic compass",
    ):
        assert question in exit_check


def test_s02_starter_and_m02_seed_package_are_unchanged():
    package = load_explorer_package(SESSIONS / "s02" / "student" / "explorer-package")

    assert package.is_loaded, package.all_issues
    compass = package.package.world_objects[0]
    assert (compass.name, compass.x, compass.y, compass.color) == (
        "Moon Compass",
        240,
        180,
        "purple",
    )


def test_s02_validation_and_trail_use_only_the_student_owned_moon_compass():
    for material in (
        SESSIONS / "s02" / "student" / "task-card.md",
        SESSIONS / "s02" / "teacher-runbook.md",
    ):
        source = _read(material)
        assert f"explore-package validate {STUDENT_MOON_COMPASS}" in source
        assert STUDENT_MOON_COMPASS in _trail_packages(source)
        command_section = source.split("explore-package validate", 1)[1]
        assert "lessons/sessions/s02/student/explorer-package" not in command_section


def test_s02_trail_adds_static_pixel_without_changing_m02_completion():
    task_card = _read(SESSIONS / "s02" / "student" / "task-card.md")
    runbook = _read(SESSIONS / "s02" / "teacher-runbook.md")
    packages = _trail_packages(task_card)

    assert packages == _trail_packages(runbook)
    assert "examples/explorer-packages/pixel-companion" in packages
    assert f'--mission-id "{MISSION_02_ID}"' in task_card

    planned = plan_local_classroom_trail(
        tuple(_source_package_path(package) for package in packages),
        player_qualified_id="nova-character:nova",
    )
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_02_ID)
    scene.enter()

    assert [npc.qualified_id for npc in scene.npcs] == ["pixel-companion:pixel"]
    assert {item.qualified_id for item in scene.objects} == {
        "moon-compass:compass",
        "crystal-lantern:lantern",
    }
    pixel = scene.npcs[0].character
    start = (pixel.x, pixel.y)

    anywhere = Bounds(min_x=-1e6, min_y=-1e6, max_x=1e6, max_y=1e6)
    for item in scene.objects:
        scene.player.move(
            item.world_object.x - scene.player.x_float,
            item.world_object.y - scene.player.y_float,
            anywhere,
        )
        scene.update(DirectionalInput(), InteractionInput(interact_pressed=True), 0.0)

    assert scene.visited_count == 2
    assert scene.mission_is_complete
    assert (pixel.x, pixel.y) == start, "Pixel must not move: no following behavior exists"


# --- Python Notes and Discovery ----------------------------------------------------------


@pytest.mark.parametrize("session", ("s01", "s02"))
def test_python_notes_follow_the_seven_part_pattern(session: str):
    notes = _read(SESSIONS / session / "student" / "python-notes.md")

    assert notes.startswith(f"# What We Learned in Python — {session.upper()}")
    positions = [notes.index(section) for section in PYTHON_NOTES_SECTIONS]
    assert positions == sorted(positions)
    assert len(notes.splitlines()) < 160, "Python Notes should stay a short page"


def test_s02_python_notes_cover_concepts_debugging_and_outside_use():
    notes = _normalized(SESSIONS / "s02" / "student" / "python-notes.md")

    for concept in ("variable", "Assignment", "string", "integer", "Coordinates"):
        assert concept in notes
    assert 'x = "240"' in notes
    assert 'TypeError: can only concatenate str (not "int") to str' in notes
    assert "Outside Explore Studio" in notes


@pytest.mark.parametrize("session", ("s01", "s02"))
def test_task_cards_link_their_python_notes(session: str):
    assert "(python-notes.md)" in _read(SESSIONS / session / "student" / "task-card.md")


def test_s02_discovery_separates_fiction_from_fact():
    discovery = _read(SESSIONS / "s02" / "student" / "discovery.md")
    fiction = discovery.split("## In Nova's world", 1)[1].split("## In our world", 1)[0]
    fact = " ".join(
        discovery.split("## In our world", 1)[1].split("## Fact or fiction?")[0].split()
    )

    assert "fictional" in fiction
    assert "fictional" not in fact.lower()
    assert "Moon Compass" not in fact
    for accurate in ("latitude", "longitude", "Before GPS", "Earth's magnetic field"):
        assert accurate in fact
    assert "Magnetic north is not exactly the" in fact
    assert len(discovery.splitlines()) < 70, "Discovery should stay a 2–4 minute segment"
    assert "(discovery.md)" in _read(SESSIONS / "s02" / "student" / "task-card.md")


# --- Website ------------------------------------------------------------------------------


def test_website_learn_route_is_data_driven_for_written_sessions_only():
    learn_data = _read(WEBSITE / "lib" / "learn.ts")
    route = WEBSITE / "app" / "students" / "learn" / "[session]" / "page.tsx"

    assert route.is_file()
    assert "generateStaticParams" in _read(route)
    assert re.findall(r'^\s+id: "(S\d\d)"', learn_data, re.MULTILINE) == [
        "S01",
        "S02",
        "S03",
        "S04",
    ]
    for heading in (
        "Python concept",
        "Code we wrote",
        "What the code means",
        "Why programmers use this",
        "What we debugged",
        "Key Python words",
        "Try it yourself",
    ):
        assert heading in _read(route)


def test_website_notes_mirror_the_student_notes_code():
    learn_data = _read(WEBSITE / "lib" / "learn.ts")

    assert 'object_name = "Moon Compass"' in learn_data
    assert "TypeError: can only concatenate str" in learn_data
    assert "unterminated string literal" in learn_data
    route = _read(WEBSITE / "app" / "students" / "learn" / "[session]" / "page.tsx")
    assert "In Nova&rsquo;s world &middot; fiction" in route
    assert "In our world &middot; fact" in route
    assert "inNovasWorld" in learn_data and "Earth's magnetic field" in learn_data


def test_existing_slide_urls_are_preserved():
    for session in ("s01", "s02", "s03", "s04"):
        page = _read(WEBSITE / "app" / "students" / "slides" / session / "page.tsx")
        assert f'canonical: "/students/slides/{session}/"' in page
        assert f"/students/learn/{session}/" in page


# --- S02 scene, destination, and ownership honesty ----------------------------------------

TEMPLATE = PROJECT_ROOT / "classroom" / "my-world-template"
TRAIL_MAP_SVG = SESSIONS / "s02" / "student" / "trail-map.svg"
TRAIL_MAP_TSX = WEBSITE / "app" / "components" / "S02TrailMap.tsx"
S02_SLIDES = WEBSITE / "app" / "students" / "slides" / "s02" / "page.tsx"
S02_MAP_PACKAGES = {
    "nova": EXAMPLES / "nova-character",
    "pixel": EXAMPLES / "pixel-companion",
    "crystal-lantern": EXAMPLES / "crystal-lantern",
    "moon-compass": SESSIONS / "s02" / "student" / "explorer-package",
}


def _package_layout() -> dict[str, tuple[int, int, str]]:
    layout = {}
    for map_id, root in S02_MAP_PACKAGES.items():
        loaded = load_explorer_package(root)
        assert loaded.is_loaded, loaded.all_issues
        (contribution,) = loaded.package.contributions
        layout[map_id] = (contribution.x, contribution.y, contribution.color)
    return layout


def test_s02_trail_maps_draw_the_real_runtime_layout():
    layout = _package_layout()

    svg = _read(TRAIL_MAP_SVG)
    drawn = {
        match["id"]: (int(match["x"]), int(match["y"]), match["color"])
        for match in re.finditer(
            r'<g id="(?P<id>[\w-]+)" data-x="(?P<x>\d+)" data-y="(?P<y>\d+)" '
            r'data-color="(?P<color>\w+)">',
            svg,
        )
    }
    assert drawn == layout

    tsx = _read(TRAIL_MAP_TSX)
    items = {
        match["id"]: (int(match["x"]), int(match["y"]), match["color"])
        for match in re.finditer(
            r'id: "(?P<id>[\w-]+)",\s+x: (?P<x>\d+),\s+y: (?P<y>\d+),\s+'
            r'size: \[\d+, \d+\],\s+color: "(?P<color>\w+)"',
            tsx,
        )
    }
    assert items == layout


def test_s02_maps_say_symbols_are_map_only_and_mark_the_destination():
    for source in (_normalized(TRAIL_MAP_SVG), " ".join(_read(TRAIL_MAP_TSX).split())):
        known_entities = ("Nova", "Pixel", "Moon Compass", "Crystal Lantern")
        assert all(name in source for name in known_entities)
        assert "simple pictures" in source
        assert "Names are not permanently drawn over characters or objects" in source
        assert "[E] Talk to Pixel" in source
        assert "labels and symbols are map-only" in source
        assert "without a known picture" in source
        assert "Crystal Lantern · the destination" in source
        assert "Moon Compass · YOU place it" in source
        assert "class example" in source


def test_s02_task_card_shows_the_map_and_distinct_object_roles():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")
    trail = task_card.split("## Your trail today", 1)[1].split("## Python first", 1)[0]
    lantern = load_explorer_package(EXAMPLES / "crystal-lantern").package.world_objects[0]

    assert "(trail-map.svg)" in trail
    assert "Moon Compass (your tool)" in trail and "**your** `x` and `y`" in trail
    assert "Crystal Lantern (the destination)" in trail
    assert lantern.when_near in trail, "quoted lantern text must be the real runtime text"
    assert "Names are not permanently drawn over characters or objects" in trail
    assert "`[E] Inspect Moon Compass`" in trail


def test_s02_materials_never_claim_the_trail_draws_names():
    for material in (
        SESSIONS / "s02" / "student" / "task-card.md",
        SESSIONS / "s02" / "teacher-runbook.md",
        S02_SLIDES,
    ):
        source = _read(material).lower()
        assert "label shown" not in source
        assert "name appears" not in source


def test_s02_value_table_separates_runtime_card_and_plan_fields():
    task_card = _read(SESSIONS / "s02" / "student" / "task-card.md")
    table = task_card.split("### What each value does today", 1)[1].split("\n\n", 2)[1]
    rows = {row.split("|")[1].strip(): row.split("|")[4].strip() for row in table.splitlines()[2:]}

    explorer_row = next(key for key in rows if key.startswith("Explorer:"))
    companion_row = next(key for key in rows if key.startswith("Companion:") and "name" in key)
    assert rows[explorer_row].startswith("No.")
    assert rows[companion_row].startswith("No.")
    assert rows["Companion: `future_ability`"] == "No. A plan for later."
    assert rows["Moon Compass: `x`, `y`"].startswith("**Yes.**")
    assert rows["Moon Compass: `name`"].startswith("No.")

    slides = _read(S02_SLIDES)
    assert '{ values: ["future_ability"], file: "companion.py", wiring: "plan" }' in slides
    assert '{ values: ["x", "y", "color"], file: "compass.yaml", wiring: "trail" }' in slides


@pytest.mark.parametrize(
    ("name", "card", "example"),
    (
        ("explorer.py", "MY EXPLORER CARD", "Nova, the class example"),
        ("companion.py", "MY COMPANION CARD", "Pixel, the class example"),
    ),
)
def test_s02_ownership_files_print_an_honest_display_only_card(name, card, example):
    completed = subprocess.run(
        [sys.executable, str(TEMPLATE / name)], capture_output=True, text=True, check=True
    )

    assert card in completed.stdout
    assert "They do not change the Trail yet." in completed.stdout
    assert example in completed.stdout
    if name == "companion.py":
        assert "PLAN for later, not built yet:" in completed.stdout


@pytest.mark.parametrize(
    "path",
    (
        SESSIONS / "s02" / "student" / "starter.py",
        TEMPLATE / "explorer.py",
        TEMPLATE / "companion.py",
    ),
)
def test_s02_student_python_stays_inside_approved_concepts(path: Path):
    """Only assignment of string/integer values and print() of names or literals."""
    for node in ast.parse(_read(path)).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # module docstring
        if isinstance(node, ast.Assign):
            assert isinstance(node.value, ast.Constant), ast.unparse(node)
            assert type(node.value.value) in (str, int), ast.unparse(node)
            continue
        assert isinstance(node, ast.Expr) and isinstance(node.value, ast.Call), ast.unparse(node)
        call = node.value
        assert isinstance(call.func, ast.Name) and call.func.id == "print", ast.unparse(node)
        assert not call.keywords, ast.unparse(node)
        for argument in call.args:
            assert isinstance(argument, (ast.Constant, ast.Name)), ast.unparse(node)


# --- S02 existing-workspace compatibility (Card format is not required) -------------------


def test_s02_student_materials_accept_both_card_and_legacy_output():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")
    notes = _normalized(SESSIONS / "s02" / "student" / "python-notes.md")

    for material in (task_card, notes):
        assert "earlier class" in material
        assert (
            "both are correct" in material.lower() or "both outputs are correct" in material.lower()
        )

    # The task card shows the legacy print-line format as valid evidence too,
    # not only the new Card format.
    assert "Explorer: Comet" in task_card
    assert "MY EXPLORER CARD" in task_card


def test_s02_student_materials_do_not_force_a_file_upgrade():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")
    notes = _normalized(SESSIONS / "s02" / "student" / "python-notes.md")

    forbidden = (
        "rerun bootstrap",
        "rerun the bootstrap",
        "run make-my-world.py again to get",
        "delete your explorer.py",
        "delete your companion.py",
        "replace your explorer.py",
        "replace your companion.py",
    )
    for material in (task_card, notes):
        lowered = material.lower()
        for phrase in forbidden:
            assert phrase not in lowered

    assert "you do not need to run `make-my-world.py` again" in task_card
    assert "you do not need" in task_card and "replace your files" in task_card


def test_s02_ownership_value_table_is_format_neutral():
    task_card = _read(SESSIONS / "s02" / "student" / "task-card.md")
    table = task_card.split("### What each value does today", 1)[1].split("\n\n", 2)[1]
    rows = {row.split("|")[1].strip(): row.split("|")[3].strip() for row in table.splitlines()[2:]}

    explorer_row = next(key for key in rows if key.startswith("Explorer:"))
    companion_row = next(key for key in rows if key.startswith("Companion:") and "name" in key)

    # The "where you see it" column must not claim the Card is the only valid
    # output; it must allow for the legacy printed-line format too.
    assert "Card" in rows[explorer_row] and "printed lines" in rows[explorer_row]
    assert "Card" in rows[companion_row] and "printed lines" in rows[companion_row]


def test_s02_teacher_runbook_check_does_not_require_two_cards():
    runbook = _normalized(SESSIONS / "s02" / "teacher-runbook.md")

    assert "two cards" not in runbook.lower()
    assert "run both files and show that their own" in runbook
    assert "the format (card vs. printed lines) is not something to check" in runbook.lower()
    assert "both are correct" in runbook.lower()


def test_s02_teacher_runbook_covers_the_returning_student_path_without_new_time():
    runbook = _read(SESSIONS / "s02" / "teacher-runbook.md")

    assert "already personalized these files in an earlier class" in runbook
    # The returning-student accommodation must live inside the existing
    # 0:18-0:27 row, not a new clock anchor.
    for anchor in (
        "0:00–0:04",
        "0:04–0:15",
        "0:15–0:18",
        "0:18–0:27",
        "0:27–0:35",
        "0:35–0:40",
        "0:40–0:43",
        "0:43–0:45",
    ):
        assert f"| {anchor} |" in runbook
    row_0_18 = [line for line in runbook.splitlines() if line.startswith("| 0:18–0:27 |")][0]
    assert "already personalized" in row_0_18


def test_s02_future_ability_stays_planning_only_regardless_of_workspace_age():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")
    notes = _normalized(SESSIONS / "s02" / "student" / "python-notes.md")
    runbook = _normalized(SESSIONS / "s02" / "teacher-runbook.md")

    assert (
        "only a plan written as text; it does not make the companion act by itself"
        in task_card.lower()
    )
    assert "does not create autonomous behavior" in notes.lower()
    assert "`future_ability` is a plan only" in runbook.lower()

    completed = subprocess.run(
        [sys.executable, str(TEMPLATE / "companion.py")], capture_output=True, text=True, check=True
    )
    assert "PLAN for later, not built yet:" in completed.stdout


def test_s02_new_workspace_templates_still_print_the_enhanced_cards():
    for name, card in (("explorer.py", "MY EXPLORER CARD"), ("companion.py", "MY COMPANION CARD")):
        completed = subprocess.run(
            [sys.executable, str(TEMPLATE / name)], capture_output=True, text=True, check=True
        )
        assert card in completed.stdout


def test_s02_bootstrap_no_overwrite_invariant_is_documented_unchanged():
    task_card = _normalized(SESSIONS / "s02" / "student" / "task-card.md")
    readme = _read(TEMPLATE / "README.md")

    assert "it only adds missing files and never replaces your work" in task_card
    assert "never" in readme.lower() and "replace" in readme.lower()
