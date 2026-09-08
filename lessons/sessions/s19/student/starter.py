"""S19: flatten nested zones and make a stable priority route."""

zones = [
    {
        "name": "Mist Shore",
        "objects": [
            {"id": "mist-bell", "priority": 2},
            {"id": "river-rune", "priority": 1},
        ],
    },
    {
        "name": "Star Ridge",
        "objects": [
            {"id": "star-lens", "priority": 2},
            {"id": "echo-shell", "priority": 3},
        ],
    },
]


def flatten_zones(zone_records):
    flattened = []
    # TODO: use one outer loop and one inner loop to append every object record.
    return flattened


def order_by_priority(records):
    # TODO: return sorted(records, key=...) without changing records in place.
    return list(records)


flat_records = flatten_zones(zones)
ordered_records = order_by_priority(flat_records)
print(flat_records)
print(ordered_records)
print(ordered_records[:3])
