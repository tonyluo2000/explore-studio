"""My editable S26 capstone source: Skyglass Observatory Expedition.

Carry forward your own S25 premise by changing story and station values. Keep
the nested ``expedition → zones → stations`` shape so your blueprint remains
easy to trace.

Safe bounds:

* use short lowercase hyphen-separated IDs;
* keep names and story messages nonempty;
* keep integer x/y coordinates from 40 through 760;
* keep route_order positive and signal_power zero or greater;
* use supported color names from existing lesson examples;
* do not add runtime/package fields here.
"""

PROJECT_EXPEDITION = {
    "name": "Skyglass Observatory",
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
                    "route_order": 2,
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
                    "enabled": False,
                    "coordinates": {"x": 620, "y": 180},
                    "color": "orange",
                    "route_order": 3,
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

SPIKE_STATION_IDS = ("echo-lens",)
