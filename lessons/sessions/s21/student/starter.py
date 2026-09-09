"""S21: return package-record diagnostics in a predictable order."""

REQUIRED_FIELDS = ("id", "name", "x", "y", "color")
ALLOWED_COLORS = {"blue", "gold", "green", "orange", "purple", "red", "yellow"}


def validate_records(records):
    """Return ordered errors: shape, fields, types, ranges, then duplicates."""
    errors = []
    seen_ids = set()
    if not isinstance(records, list):
        return ["records: expected a list"]

    for number, record in enumerate(records, start=1):
        label = f"record {number}"
        if not isinstance(record, dict):
            errors.append(f"{label}: expected a dictionary")
            continue

        for field in REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"{label}: missing {field}")

        if "id" in record and not isinstance(record["id"], str):
            errors.append(f"{label}: id must be text")
        if "name" in record and not isinstance(record["name"], str):
            errors.append(f"{label}: name must be text")
        for field in ("x", "y"):
            if field in record and not isinstance(record[field], int):
                errors.append(f"{label}: {field} must be an integer")
        for field in ("x", "y"):
            if isinstance(record.get(field), int) and not 40 <= record[field] <= 760:
                errors.append(f"{label}: {field} must be from 40 to 760")
        if "color" in record and not isinstance(record["color"], str):
            errors.append(f"{label}: color must be text")
        elif "color" in record and record["color"] not in ALLOWED_COLORS:
            errors.append(f"{label}: unsupported color {record['color']!r}")

        record_id = record.get("id")
        if isinstance(record_id, str):
            if record_id in seen_ids:
                errors.append(f"{label}: duplicate id {record_id!r}")
            seen_ids.add(record_id)
    return errors


CASES = [
    (
        "valid",
        [{"id": "map", "name": "Map", "x": 220, "y": 180, "color": "gold"}],
        [],
    ),
    (
        "malformed",
        [
            {"id": "map", "name": "Map", "x": 20, "y": "180", "color": "teal"},
            {"id": "map", "x": 240, "y": 180, "color": "gold"},
        ],
        [
            "record 1: y must be an integer",
            "record 1: x must be from 40 to 760",
            "record 1: unsupported color 'teal'",
            "record 2: missing name",
            "record 2: duplicate id 'map'",
        ],
    ),
]


def main():
    for name, records, expected in CASES:
        actual = validate_records(records)
        print(name, actual)
        assert actual == expected
    # TODO: add one table row for a non-dictionary record before editing the validator.


if __name__ == "__main__":
    main()
