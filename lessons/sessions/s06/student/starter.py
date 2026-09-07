"""S06: print an inventory from exactly three object dictionaries."""

objects = [
    {"name": "Sun Seed", "x": 180, "y": 180, "color": "gold"},
    {"name": "Rain Bell", "x": 380, "y": 300, "color": "blue"},
    {"name": "TODO: third garden object", "x": 620, "y": 420, "color": "green"},
]

for object_record in objects:
    print(
        object_record["name"],
        object_record["x"],
        object_record["y"],
        object_record["color"],
    )
