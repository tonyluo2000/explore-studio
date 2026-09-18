"""S23 monolith: preserve output while moving helpers into bounded modules."""

from pathlib import Path

import yaml

INPUT_PATH = Path(__file__).parent / "workshop-plan.yaml"
MY_SYSTEM_PATH = Path(__file__).parent / "my-system.yaml"
PLACEHOLDER = "CHOOSE-ME"


def load_data(path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def validate_data(plan):
    errors = []
    if not isinstance(plan, dict):
        return ["plan must be a dictionary"]
    for key in ("package", "style", "objects", "keeper"):
        if key not in plan:
            errors.append(f"missing {key}")
    objects = plan.get("objects")
    if isinstance(objects, list) and len(objects) != 2:
        errors.append("exactly two objects are required")
    keeper = plan.get("keeper")
    if isinstance(keeper, dict) and isinstance(objects, list):
        object_ids = [record.get("id") for record in objects if isinstance(record, dict)]
        if keeper.get("watches") not in object_ids:
            errors.append("keeper must watch one of this plan's objects")
        if keeper.get("when_off") == keeper.get("when_on"):
            errors.append("keeper off and on lines must differ")
    return errors


def build_output(plan):
    style = plan["style"]
    keeper = plan["keeper"]
    contributions = []
    documents = {}
    for record in plan["objects"]:
        path = f"objects/{record['id']}.yaml"
        contributions.append({"id": record["id"], "type": "world_object", "path": path})
        documents[path] = {
            "name": record["name"],
            "x": record["x"],
            "y": record["y"],
            "when_near": "Two builders share one careful design.",
            "when_interacted": "The shared workshop style changes.",
            "toggle_style_id": style["id"],
        }
    keeper_path = f"character/{keeper['id']}.yaml"
    contributions.append({"id": keeper["id"], "type": "character", "path": keeper_path})
    documents[keeper_path] = {
        "name": keeper["name"],
        "x": keeper["x"],
        "y": keeper["y"],
        "color": keeper["color"],
        "respond_to_toggle": {
            "object_id": keeper["watches"],
            "when_off": keeper["when_off"],
            "when_on": keeper["when_on"],
        },
    }
    manifest = {
        "schema_version": "0.2",
        "package": plan["package"],
        "compatibility": {"student_api": "0.1"},
        "toggle_styles": [style],
        "contributions": contributions,
    }
    return {"manifest.yaml": manifest, **documents}


def render_output(documents):
    sections = []
    for path in sorted(documents):
        text = yaml.safe_dump(documents[path], sort_keys=False, allow_unicode=True).strip()
        sections.append(f"--- {path} ---\n{text}")
    return "\n".join(sections) + "\n"


def pipeline_text(path=INPUT_PATH):
    # TODO: draw the call/data flow, then move these three responsibilities into
    # data_io.py, rules.py, and build_output.py without changing this result.
    plan = load_data(path)
    errors = validate_data(plan)
    if errors:
        raise ValueError(errors)
    return render_output(build_output(plan))


def compose_text():
    """Build your own system from my-system.yaml using the same pipeline."""
    # TODO: replace every CHOOSE-ME in my-system.yaml, then run this.
    if PLACEHOLDER in MY_SYSTEM_PATH.read_text(encoding="utf-8"):
        raise ValueError(f"my-system.yaml still contains {PLACEHOLDER}")
    return pipeline_text(MY_SYSTEM_PATH)


if __name__ == "__main__":
    print(pipeline_text(), end="")
