"""My editable S27 nested capstone plan: Skyglass Observatory."""

PROJECT_PLAN = {
    "name": "Skyglass Observatory",
    "package": {
        "id": "skyglass-core",
        "display_name": "Skyglass Observatory Core",
        "toggle_style": {
            "id": "observatory-glow",
            "off_color": "blue",
            "on_color": "gold",
        },
    },
    "required_station_ids": ("echo-lens", "wind-dial", "comet-bell"),
    "zones": [
        {
            "id": "lower-deck",
            "name": "Lower Deck",
            "stations": [
                {
                    "id": "echo-lens",
                    "name": "Echo Lens",
                    "enabled": True,
                    "coordinates": {"x": 260, "y": 300},
                    "color": "purple",
                    "toggle_style_id": "observatory-glow",
                    "route_order": 1,
                    "signal_power": 3,
                    "story": {
                        "when_near": "The Echo Lens hums with captured starlight.",
                        "when_interacted": "You align the Echo Lens with the night sky!",
                    },
                },
                {
                    "id": "wind-dial",
                    "name": "Wind Dial",
                    "enabled": True,
                    "coordinates": {"x": 460, "y": 250},
                    "color": "blue",
                    "toggle_style_id": "observatory-glow",
                    "route_order": 1,
                    "signal_power": 2,
                    "story": {
                        "when_near": "The Wind Dial turns toward a quiet constellation.",
                        "when_interacted": "You record the observatory wind direction.",
                    },
                },
            ],
        },
        {
            "id": "upper-deck",
            "name": "Upper Deck",
            "stations": [
                {
                    "id": "comet-bell",
                    "name": "Comet Bell",
                    "enabled": True,
                    "coordinates": {"x": 620, "y": 180},
                    "color": "orange",
                    "route_order": 2,
                    "signal_power": 4,
                    "story": {
                        "when_near": "The Comet Bell waits beneath the open dome.",
                        "when_interacted": "The bell answers with one bright note.",
                    },
                }
            ],
        },
    ],
}
