"""S24: compare repeated record scans with one ID dictionary."""


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


def main():
    print("small:", compare(6))
    print("larger:", compare(12))
    assert compare(6)[:2] == (15, 6)
    # TODO: predict, then add the equivalent inspection-count assertion for 12.


if __name__ == "__main__":
    main()
