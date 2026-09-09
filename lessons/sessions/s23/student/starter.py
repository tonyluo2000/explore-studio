"""S23 monolith: preserve output while moving helpers into bounded modules."""

from pathlib import Path

import yaml

INPUT_PATH = Path(__file__).parent / "workshop-plan.yaml"


def load_data(path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def validate_data(plan):
    errors = []
    if not isinstance(plan, dict):
        return ["plan must be a dictionary"]
    for key in ("package", "style", "objects"):
        if key not in plan:
            errors.append(f"missing {key}")
    if isinstance(plan.get("objects"), list) and len(plan["objects"]) != 2:
        errors.append("exactly two objects are required")
    return errors


def build_output(plan):
    style = plan["style"]
    contributions = []
    objects = {}
    for record in plan["objects"]:
        path = f"objects/{record['id']}.yaml"
        contributions.append({"id": record["id"], "type": "world_object", "path": path})
        objects[path] = {
            "name": record["name"],
            "x": record["x"],
            "y": record["y"],
            "when_near": "Two builders share one careful design.",
            "when_interacted": "The shared workshop style changes.",
            "toggle_style_id": style["id"],
        }
    manifest = {
        "schema_version": "0.2",
        "package": plan["package"],
        "compatibility": {"student_api": "0.1"},
        "toggle_styles": [style],
        "contributions": contributions,
    }
    return {"manifest.yaml": manifest, **objects}


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


if __name__ == "__main__":
    print(pipeline_text(), end="")
