"""S24: compare repeated record scans with one ID dictionary, then polish."""

ROUTE = (
    {"id": "signal-map", "name": "Signal Map", "position": "first"},
    {"id": "river-token", "name": "River Token", "position": "second"},
    {"id": "summit-bell", "name": "Summit Bell", "position": "third"},
)


def find_many_by_scan(records, wanted_ids):
    found = []
    inspections = 0
    for wanted_id in wanted_ids:
        match = None
        for record in records:
            inspections += 1
            if record["id"] == wanted_id:
                match = record
                break
        found.append(match)
    return found, inspections


def build_id_index(records):
    index = {}
    inspections = 0
    for record in records:
        inspections += 1
        record_id = record["id"]
        if record_id in index:
            raise ValueError(f"duplicate id: {record_id}")
        index[record_id] = record
    return index, inspections


def find_many_by_index(records, wanted_ids):
    index, inspections = build_id_index(records)
    return [index.get(wanted_id) for wanted_id in wanted_ids], inspections


def make_catalog(size):
    records = []
    for number in range(1, size + 1):
        records.append({"id": f"clue-{number}", "name": f"Clue {number}"})
    return records


def compare(size):
    records = make_catalog(size)
    wanted_ids = [f"clue-{size - 2}", f"clue-{size - 1}", f"clue-{size}"]
    scanned, scan_count = find_many_by_scan(records, wanted_ids)
    indexed, index_count = find_many_by_index(records, wanted_ids)
    assert scanned == indexed
    return scan_count, index_count, [record["id"] for record in indexed]


def route_briefing():
    """Player-facing route briefing. Correct, and harder to read than it needs to be."""
    out = []
    r0 = ROUTE[0]
    t0 = "Visit " + r0["name"] + " " + r0["position"] + "."
    out.append(t0)
    r1 = ROUTE[1]
    t1 = "Visit " + r1["name"] + " " + r1["position"] + "."
    out.append(t1)
    r2 = ROUTE[2]
    t2 = "Visit " + r2["name"] + " " + r2["position"] + "."
    out.append(t2)
    return out


def behavior_signature():
    """Everything that must be identical before and after your improvement."""
    return (compare(6), compare(12), tuple(route_briefing()))


def main():
    print("small:", compare(6))
    print("larger:", compare(12))
    assert compare(6)[:2] == (15, 6)
    # TODO: predict, then add the equivalent inspection-count assertion for 12.
    for line in route_briefing():
        print(line)
    # TODO: record behavior_signature(), improve route_briefing (one loop, clearer
    # names, no copy-paste), then prove the signature is unchanged.


if __name__ == "__main__":
    main()
