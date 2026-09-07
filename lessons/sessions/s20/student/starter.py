"""S20: build a deterministic current-contract package from local YAML."""

from pathlib import Path

import yaml

STUDENT_ROOT = Path(__file__).parent
INPUT_PATH = STUDENT_ROOT / "mystery-plan.yaml"
OUTPUT_ROOT = STUDENT_ROOT / "explorer-package"


def load_plan(path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def valid_record(record):
    if not isinstance(record, dict):
        return False
    required_keys = ("id", "name", "x", "y", "color", "priority", "include")
    for key in required_keys:
        if key not in record:
            return False
    # TODO: add the expected type/range checks for every required key.
    return isinstance(record["id"], str)


def selected_records(records):
    matches = []
    for record in records:
        if record["include"]:
            matches.append(record)
    return matches


def priority_total(records):
    priorities = []
    for record in records:
        priorities.append(record["priority"])
    return sum(priorities)


def ordered_records(records):
    return sorted(records, key=lambda record: record["priority"])


def object_document(record):
    return {
        "name": record["name"],
        "x": record["x"],
        "y": record["y"],
        "color": record["color"],
        "when_near": f"You sense a clue near the {record['name']}.",
        "when_interacted": f"You study the {record['name']}.",
    }


def write_yaml(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
    path.write_text(text, encoding="utf-8")


def build_package(plan, output_root):
    records = plan["objects"]
    records_are_valid = True
    for record in records:
        if not valid_record(record):
            records_are_valid = False
    if len(records) < 3 or not records_are_valid:
        raise ValueError("objects must contain at least three valid records")

    selected = selected_records(records)
    ordered = ordered_records(selected)
    if len(ordered) != 3:
        raise ValueError("exactly three included records are required")

    package = plan["package"]
    keeper = plan["keeper"]
    contributions = []
    for record in ordered:
        contributions.append(
            {"id": record["id"], "type": "world_object", "path": f"objects/{record['id']}.yaml"}
        )
        write_yaml(output_root / "objects" / f"{record['id']}.yaml", object_document(record))

    contributions.append(
        {"id": keeper["id"], "type": "character", "path": f"character/{keeper['id']}.yaml"}
    )
    manifest = {
        "schema_version": "0.1",
        "package": package,
        "compatibility": {"student_api": "0.1"},
        "contributions": contributions,
    }
    sequence_ids = []
    for record in ordered:
        sequence_ids.append(record["id"])
    character = {
        "name": keeper["name"],
        "x": keeper["x"],
        "y": keeper["y"],
        "color": keeper["color"],
        "respond_to_sequence": {
            "object_ids": sequence_ids,
            "when_incomplete": keeper["when_incomplete"],
            "when_complete": keeper["when_complete"],
        },
    }
    write_yaml(output_root / "manifest.yaml", manifest)
    write_yaml(output_root / "character" / f"{keeper['id']}.yaml", character)
    return ordered


def main():
    plan = load_plan(INPUT_PATH)
    ordered = build_package(plan, OUTPUT_ROOT)
    print("Loaded", len(plan["objects"]), "records")
    print("Selected", len(ordered), "records")
    print("Priority total:", priority_total(ordered))
    sequence_ids = []
    for record in ordered:
        sequence_ids.append(record["id"])
    print("Sequence:", sequence_ids)
    # TODO: add assertions for normal, exactly-three boundary, and malformed record cases.


if __name__ == "__main__":
    main()
