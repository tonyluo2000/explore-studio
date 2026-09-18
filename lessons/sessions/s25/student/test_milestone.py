"""S25 Milestone B checker — is my playable prototype actually finished?

Run it whenever you want to know where you stand:

```console
python -m pytest -q lessons/sessions/s25/student/test_milestone.py
```

Every failure here is one of three different things, and the test name tells
you which:

* ``test_plan_*`` / ``test_*_is_authored`` / ``test_reflection_*`` — a decision
  you have not made yet. Nothing is broken; a ``CHOOSE-ME`` is still sitting
  where your words belong.
* ``test_pipeline_*`` — the four TODO functions in ``starter.py`` are not
  finished yet. These run your pipeline against the fixed ``fixtures.py``
  catalogs; ``test_pipeline.py`` says the same thing in smaller pieces.
* ``test_package_validates`` / ``test_package_loads_and_plans`` — your package
  is invalid. Read the diagnostic; it names the file and the field.
* ``test_two_supported_mechanics`` / ``test_second_mechanic_is_wired`` /
  ``test_build_is_deterministic`` — the prototype is missing the composition or
  the build evidence the milestone asks for.

This checker never inspects your premise, your names, or your story. It only
asks whether you made the decisions and whether the result really runs.
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from explore.packages.classroom_trail import plan_local_classroom_trail
from explore.packages.explorer_package_export import export_explorer_package
from explore.packages.loader import load_explorer_package

PLACEHOLDER = "CHOOSE-ME"
STUDENT_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
MILESTONE_PATH = STUDENT_ROOT / "milestone.yaml"
CATALOG_PATH = STUDENT_ROOT / "project_catalog.py"
STARTER_PATH = STUDENT_ROOT / "starter.py"
FIXTURES_PATH = STUDENT_ROOT / "fixtures.py"


def _nova_root() -> Path:
    """Find the shipped Nova example, whatever the course folder is called."""
    for parent in STUDENT_ROOT.parents:
        candidate = parent / "examples" / "explorer-packages" / "nova-character"
        if candidate.is_dir():
            return candidate
    raise AssertionError("examples/explorer-packages/nova-character is missing")


#: Mechanic two may be any of these. They are the supported state mechanics a
#: character can read, which is what makes two mechanics a system rather than
#: two examples side by side.
SECOND_MECHANIC_KINDS = ("counter", "toggle", "two_toggles", "either_toggle")


def _unfilled(value, path="") -> list[str]:
    """Return the dotted paths of every value still holding a placeholder."""
    if isinstance(value, str):
        return [path] if PLACEHOLDER in value else []
    if isinstance(value, dict):
        return [
            item
            for key, child in value.items()
            for item in _unfilled(child, f"{path}.{key}" if path else str(key))
        ]
    if isinstance(value, (list, tuple)):
        return [
            item
            for index, child in enumerate(value)
            for item in _unfilled(child, f"{path}[{index}]")
        ]
    return []


@pytest.fixture(scope="module")
def milestone() -> dict:
    document = yaml.safe_load(MILESTONE_PATH.read_text(encoding="utf-8"))
    assert isinstance(document, dict), f"{MILESTONE_PATH.name} must stay a YAML mapping"
    return document


@pytest.fixture(scope="module")
def catalog() -> dict:
    return runpy.run_path(str(CATALOG_PATH))


@pytest.fixture(scope="module")
def pipeline():
    return _student_module(STARTER_PATH)


@pytest.fixture(scope="module")
def fixtures():
    return _student_module(FIXTURES_PATH)


@pytest.fixture(scope="module")
def loaded():
    return load_explorer_package(PACKAGE_ROOT)


@pytest.fixture(scope="module")
def package(loaded):
    if not loaded.is_loaded:
        pytest.skip("package is not valid yet; fix test_package_validates first")
    return loaded.package


def _student_module(path: Path):
    """Import one of my own files by path, so this works in any course folder."""
    if str(STUDENT_ROOT) not in sys.path:
        sys.path.insert(0, str(STUDENT_ROOT))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def _mechanic_families(package) -> set[str]:
    """Return which supported mechanic families this package actually contains."""
    families = set()
    if any(character.respond_to_sequence is not None for character in package.characters):
        families.add("sequence")
    if any(item.counter is not None for item in package.world_objects):
        families.add("counter")
    if any(item.toggle is not None for item in package.world_objects):
        families.add("toggle")
    if any(
        character.greeting is not None or character.conversation is not None
        for character in package.characters
    ):
        families.add("dialogue")
    return families


# --- Did I make my decisions? ------------------------------------------------


def test_plan_is_authored_before_the_build(milestone):
    plan = milestone.get("plan")
    assert isinstance(plan, dict), "milestone.yaml needs a `plan:` mapping"
    missing = _unfilled(plan, "plan")
    assert not missing, (
        "Your plan still has unmade decisions: "
        + ", ".join(missing)
        + ". Write them in milestone.yaml before you author the package."
    )
    assert plan["mechanics"][0] == "sequence", "mechanic one is the M15 ordered route"
    assert plan["mechanics"][1] in SECOND_MECHANIC_KINDS, (
        f"plan.mechanics[1] must be one of {SECOND_MECHANIC_KINDS}; "
        f"got {plan['mechanics'][1]!r}"
    )


def test_catalog_choices_are_authored(catalog):
    missing = _unfilled(catalog["PROJECT_CATALOG"], "PROJECT_CATALOG")
    missing += _unfilled(catalog["SECOND_MECHANIC"], "SECOND_MECHANIC")
    assert not missing, (
        "project_catalog.py still holds placeholders: "
        + ", ".join(missing)
        + ". Those are your premise, your names, and your second-mechanic plan."
    )
    assert (
        catalog["SECOND_MECHANIC"]["kind"] in SECOND_MECHANIC_KINDS
    ), f"SECOND_MECHANIC['kind'] must be one of {SECOND_MECHANIC_KINDS}"


def test_package_text_is_authored():
    """Every authored string in the package YAML must be in the student's words."""
    unfilled = []
    for path in sorted(PACKAGE_ROOT.rglob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        unfilled += [f"{relative}:{field}" for field in _unfilled(document)]
    assert not unfilled, (
        "Your package still speaks in placeholders: "
        + ", ".join(unfilled)
        + ". A visitor reads these lines; write them yourself."
    )


# --- Did I finish the pipeline? ----------------------------------------------


def _required_stations(fixtures) -> list[dict]:
    """The three prepared stations REQUIRED_IDS asks for, in requested order."""
    by_id = {
        station["id"]: station
        for region in fixtures.NORMAL_CATALOG["regions"]
        for station in region["stations"]
    }
    return [by_id[required] for required in fixtures.REQUIRED_IDS]


def test_pipeline_selects_aggregates_and_orders_the_route(pipeline, fixtures):
    """The TODO functions have to really search, count, aggregate, and sort."""
    required = _required_stations(fixtures)
    try:
        result = pipeline.build_preview(fixtures.NORMAL_CATALOG, fixtures.REQUIRED_IDS)
    except ValueError as error:
        pytest.fail(
            "Your pipeline refused the prepared normal catalog, which is valid:\n"
            f"  {error}\n"
            "Finish the TODO bodies in starter.py. test_pipeline.py checks the "
            "same stages one at a time."
        )
    assert result["selected_count"] == 3, "select_route must return exactly three stations"
    assert result["signal_power"] == sum(
        station["signal_power"] for station in required
    ), "signal_total must add the signal_power of the selected stations"
    assert result["preview"]["route_ids"] == [
        station["id"] for station in sorted(required, key=lambda item: item["route_order"])
    ], "ordered_route must return a stable sorted copy keyed on route_order only"
    assert len(result["preview"]["objects"]) == 3


def test_pipeline_refuses_invalid_and_absent_stations(pipeline, fixtures):
    """Bad data has to stop the pipeline before anything is previewed."""
    healthy = _required_stations(fixtures)[0]
    assert (
        pipeline.validate_station(healthy) == []
    ), f"validate_station rejected a prepared valid station: {pipeline.validate_station(healthy)}"

    malformed = [
        station
        for region in fixtures.MALFORMED_COORDINATE_CATALOG["regions"]
        for station in region["stations"]
        if not isinstance(station["world"]["x"], int)
    ]
    assert malformed, "fixtures.py must keep one station whose world.x is text"
    assert pipeline.validate_station(malformed[0]), (
        "validate_station accepted a station whose world.x is text, not an integer. "
        "Return an error for every rule the task card lists."
    )

    with pytest.raises(ValueError):
        pipeline.build_preview(fixtures.MALFORMED_COORDINATE_CATALOG, fixtures.REQUIRED_IDS)
    with pytest.raises(ValueError):
        pipeline.select_route(fixtures.ABSENT_REQUIRED_CATALOG, fixtures.REQUIRED_IDS)


# --- Is the package real? ----------------------------------------------------


def test_package_validates(loaded):
    assert loaded.is_loaded, "explore-package validate rejected your package:\n" + "\n".join(
        f"  {issue.code.value}: {issue.location}: {issue.message}" for issue in loaded.all_issues
    )


def test_package_loads_and_plans_for_trail(package):
    planned = plan_local_classroom_trail(
        (_nova_root(), PACKAGE_ROOT), player_qualified_id="nova-character:nova"
    )
    assert (
        planned.is_planned
    ), "your package validates but cannot be planned for Trail:\n" + "\n".join(
        f"  {issue.code.value}: {issue.location}: {issue.message}" for issue in planned.issues
    )


# --- Do two mechanics coexist, and do they mean anything together? -----------


def test_route_keeper_still_owns_an_exact_three_step_sequence(package):
    sequences = [
        character.respond_to_sequence
        for character in package.characters
        if character.respond_to_sequence is not None
    ]
    assert len(sequences) == 1, "keep exactly one ordered-route keeper (M15 stays at three steps)"
    assert len(sequences[0].object_ids) == 3
    object_ids = {item.contribution_id for item in package.world_objects}
    assert (
        set(sequences[0].object_ids) <= object_ids
    ), "the keeper watches an object that is not here"


def test_two_supported_mechanics_are_present(package):
    families = _mechanic_families(package)
    assert "sequence" in families, "mechanic one is the M15 ordered route; keep it"
    second = families - {"sequence", "dialogue"}
    assert second, (
        "Milestone B needs TWO mechanics and your package has one (the ordered route). "
        "Add your chosen second mechanic: a `counter:` block or a `toggle:` block on one "
        "object, plus the character that reads it. Dialogue alone does not count."
    )


def test_second_mechanic_is_wired_into_the_world(package, catalog):
    """Two mechanics must meet somewhere: a reader, or a shared object."""
    kind = catalog["SECOND_MECHANIC"]["kind"]
    carrier_id = catalog["SECOND_MECHANIC"]["object_id"]
    carriers = {
        item.contribution_id
        for item in package.world_objects
        if (item.counter is not None if kind == "counter" else item.toggle is not None)
    }
    assert carrier_id in carriers, (
        f"SECOND_MECHANIC says {carrier_id!r} carries your {kind}, but the package does not "
        f"give it one. Objects that do: {sorted(carriers) or 'none'}."
    )

    readers = [
        character
        for character in package.characters
        if character.respond_to_counter is not None
        or character.respond_to_toggle is not None
        or character.respond_to_two_toggles is not None
        or character.respond_to_either_toggle is not None
    ]
    route = next(
        character.respond_to_sequence.object_ids
        for character in package.characters
        if character.respond_to_sequence is not None
    )
    assert readers or carrier_id in route, (
        "Your second mechanic is decoration right now: nothing reads it and it does not sit "
        "on the route. Either add a character that responds to it, or move it onto one of "
        f"your three route objects ({', '.join(route)})."
    )


# --- Does it build the same way twice? ---------------------------------------


def _export(destination: Path, package) -> str:
    metadata = package.metadata
    # `.resolve()` because the exporter refuses a destination reached through a
    # symlink, and a temporary directory is one on macOS.
    archive = destination.resolve() / f"{metadata.id}-{metadata.version}.explorer-package.zip"
    result = export_explorer_package(PACKAGE_ROOT, archive)
    assert result.is_exported, "\n".join(
        f"  {issue.code.value}: {issue.location}: {issue.message}" for issue in result.issues
    )
    assert result.digest is not None
    return result.digest.hex_digest


def test_build_is_deterministic(package):
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        assert _export(Path(first), package) == _export(
            Path(second), package
        ), "the same package produced two different archives"


def test_pasted_evidence_matches_this_package(milestone, package):
    evidence = milestone.get("evidence")
    assert isinstance(evidence, dict), "milestone.yaml needs an `evidence:` mapping"
    missing = _unfilled(evidence, "evidence")
    assert not missing, (
        "Milestone evidence is still blank: "
        + ", ".join(missing)
        + ". Paste it from your own terminal."
    )
    assert package.metadata.id in evidence["package_validation"], (
        "evidence.package_validation should be the line `explore-package validate` printed, "
        f"which names {package.metadata.id}."
    )
    with tempfile.TemporaryDirectory() as destination:
        expected = _export(Path(destination), package)
    assert evidence["build_digest"].strip() == expected, (
        "evidence.build_digest does not match your package as it stands now. "
        f"Re-export and paste the current digest:\n  {expected}"
    )


# --- Can I explain it? -------------------------------------------------------


def test_reflection_is_complete(milestone):
    reflection = milestone.get("reflection")
    assert isinstance(reflection, dict), "milestone.yaml needs a `reflection:` mapping"
    missing = _unfilled(reflection, "reflection")
    assert not missing, (
        "Your reflection is unfinished: "
        + ", ".join(missing)
        + ". One or two sentences each is enough."
    )
    problem = reflection["problem_and_how_i_fixed_it"]
    assert len(problem.split()) >= 8, (
        "Name one real problem and the one change that fixed it — "
        "what you saw, and what you changed."
    )


def test_reflection_explains_one_design_and_one_technical_decision(milestone):
    """Criterion 7: one decision about the experience, one about how you built it."""
    reflection = milestone.get("reflection")
    assert isinstance(reflection, dict), "milestone.yaml needs a `reflection:` mapping"
    for field in ("design_decision", "technical_decision"):
        assert field in reflection, f"milestone.yaml needs a `reflection.{field}:` line"
        answer = reflection[field]
        assert isinstance(answer, str) and answer.strip(), (
            f"reflection.{field} is blank. Criterion 7 asks for one design decision "
            "and one technical decision; one sentence each is enough."
        )
        assert PLACEHOLDER not in answer, (
            f"reflection.{field} still says {PLACEHOLDER}. "
            "Name the decision you actually made, and why."
        )
