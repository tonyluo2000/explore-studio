"""Teacher-prepared practice code. Keep separate from the real capstone."""


def shape_records(records):
    shaped = []
    for record in records:
        item = {
            "id": record["id"],
            "label": record["name"].strip(),
            "enabled": record.get("enabled", True),
        }
        shaped.append(item)
    return shaped


def shape_enabled_records(records):
    shaped = []
    for record in records:
        item = {
            "id": record["id"],
            "label": record["name"].strip(),
            "enabled": record.get("enabled", True),
        }
        if item["enabled"]:
            shaped.append(item)
    return shaped


def run(x, enabled_only=False, include_count=False):
    """Deliberately confusing practice target with several responsibilities."""
    if not isinstance(x, list):
        raise ValueError("records must be a list")
    records = shape_enabled_records(x) if enabled_only else shape_records(x)
    if include_count:
        return {"records": records, "count": len(records)}
    return records
