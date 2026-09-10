"""S28 narrow, intentionally incomplete local package integration boundary."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from lessons.sessions.s27.student import builder as s27_builder
from lessons.sessions.s27.student import data_io as s27_data_io
from lessons.sessions.s27.student import rules as s27_rules
from lessons.sessions.s27.student import validation as s27_validation

STUDENT_ROOT = Path(__file__).parent.resolve()
SOURCE_PLAN_PATH = STUDENT_ROOT / "source-plan.yaml"
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
SAFE_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class InputPlanError(ValueError):
    """The explicit local input path could not be read safely."""


class CorruptPlanError(ValueError):
    """The local input file is not valid safe YAML."""


class InvalidPlanError(ValueError):
    """The loaded plan failed deterministic semantic validation."""


class UnsafeIdentifierError(ValueError):
    """A contribution ID cannot safely influence an output path."""


def safe_object_output_path(contribution_id):
    """Return one confined object path after validating the ID first."""
    if not isinstance(contribution_id, str) or SAFE_IDENTIFIER.fullmatch(contribution_id) is None:
        raise UnsafeIdentifierError(f"unsafe contribution id: {contribution_id!r}")
    return PACKAGE_ROOT / "objects" / f"{contribution_id}.yaml"


def load_plan(source_path=SOURCE_PLAN_PATH):
    """Load one explicit local YAML plan with narrow named errors."""
    path = Path(source_path)
    # TODO: resolve and confine path under STUDENT_ROOT before opening, then
    # require the expected mapping/list container shape after safe_load.
    try:
        with path.open(encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
    except FileNotFoundError as error:
        raise InputPlanError(f"missing input file: {path.name}") from error
    except yaml.YAMLError as error:
        raise CorruptPlanError(f"corrupt YAML data: {path.name}") from error
    return loaded


def write_yaml(output_path, document):
    """Render deterministic YAML; TODO: confine and write it as UTF-8 bytes."""
    rendered = yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
    # TODO: resolve output_path beneath PACKAGE_ROOT, create only its parent,
    # write the encoded bytes, and return those exact bytes as evidence.
    return rendered.encode("utf-8")


def build_package(plan):
    """TODO: reuse S27 helpers, safely write all documents, and validate output."""
    diagnostics = s27_validation.validate_plan(plan)
    if diagnostics:
        raise InvalidPlanError("; ".join(diagnostics))
    stations = s27_data_io.flatten_stations(plan)
    found = s27_rules.find_required(stations, plan["required_station_ids"])
    selected = s27_rules.select_enabled(found)
    _signal_power = s27_rules.signal_total(selected)
    ordered = s27_rules.order_route(selected)
    _documents = s27_builder.build_documents(plan, ordered)
    # TODO: validate every object/guide ID before constructing paths; add the
    # existing sequence document; write the stable file list; validate package;
    # preserve diagnostics; return output path, files, and validation evidence.
    return {
        "output_root": str(PACKAGE_ROOT),
        "generated_files": (),
        "validation_issues": (),
    }
