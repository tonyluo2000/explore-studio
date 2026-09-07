"""S14: reuse one named style in two object descriptions."""


def build_switch(name, x, y, style):
    return {"name": name, "x": x, "y": y, "style": style}


shared_style = {"off_color": "purple", "on_color": "gold"}

north_switch = build_switch("North Beacon", 260, 220, shared_style)
# TODO: replace the duplicated inline style below with shared_style.
south_switch = build_switch(
    "South Beacon",
    500,
    380,
    {"off_color": "purple", "on_color": "gold"},
)

print(north_switch)
print(south_switch)
