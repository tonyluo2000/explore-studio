"""S16: diagnose three record-shape problems one at a time."""

records = [
    {"id": "sun-dial", "name": "Sun Dial", "color": "gold"},
    {"id": "sun-dial", "name": "Rain Jar", "color": "blue"},
    {"object": {"id": "moss-map", "name": "Moss Map", "color": "green"}},
]

seen_ids = []
for number, record in enumerate(records, start=1):
    if "id" not in record:
        print(number, "incorrect nesting: id is not at the record level")
    else:
        if record["id"] in seen_ids:
            print(number, "duplicate ID:", record["id"])
        else:
            seen_ids.append(record["id"])
        if "zone" not in record:
            print(number, "missing key: zone")

# TODO: repair one record at a time and rerun until no diagnostic prints.
