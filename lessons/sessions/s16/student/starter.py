"""S16: build a numbered curator catalog from object records."""

objects = [
    {"id": "sun-dial", "name": "Sun Dial", "color": "gold", "zone": "Dawn"},
    {"id": "rain-jar", "name": "Rain Jar", "color": "blue", "zone": "Cloud"},
    {"id": "moss-map", "name": "Moss Map", "color": "green", "zone": "Grove"},
]

for number, record in enumerate(objects, start=1):
    # TODO: add the record's zone to the readable catalog line.
    print(f"{number}. {record['name']} [{record['id']}] — {record['color']}")
