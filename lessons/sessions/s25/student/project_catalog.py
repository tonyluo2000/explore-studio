"""My editable S25 project source: Moonlit Garden Route.

Change the story values below, then make the same reviewed changes in
``explorer-package/``. Keep exactly three stations for the core route.

Safe bounds:

* keep every ``id`` short, lowercase, and hyphen-separated;
* keep names and messages nonempty;
* keep ``x`` and ``y`` integers from 40 through 760;
* keep ``signal_power`` at zero or greater;
* keep ``route_order`` values positive and use 1, 2, and 3 for a clear route;
* use supported color names already seen in the lesson examples.
"""

PROJECT_ROUTE_IDS = ("seed-marker", "brook-chime", "moon-bloom")

PROJECT_CATALOG = {
    "regions": [
        {
            "name": "Moonlit Garden",
            "stations": [
                {
                    "id": "seed-marker",
                    "name": "Seed Marker",
                    "enabled": True,
                    "route_order": 1,
                    "signal_power": 2,
                    "world": {
                        "x": 180,
                        "y": 310,
                        "color": "green",
                        "when_near": "A carved seed points toward the garden path.",
                        "when_interacted": "The first garden clue is ready.",
                    },
                },
                {
                    "id": "brook-chime",
                    "name": "Brook Chime",
                    "enabled": True,
                    "route_order": 2,
                    "signal_power": 3,
                    "world": {
                        "x": 390,
                        "y": 230,
                        "color": "blue",
                        "when_near": "A silver chime rings beside the brook.",
                        "when_interacted": "The second garden clue begins to sing.",
                    },
                },
                {
                    "id": "moon-bloom",
                    "name": "Moon Bloom",
                    "enabled": True,
                    "route_order": 3,
                    "signal_power": 4,
                    "world": {
                        "x": 610,
                        "y": 350,
                        "color": "purple",
                        "when_near": "A moonlit flower opens at the end of the path.",
                        "when_interacted": "The final garden clue glows.",
                    },
                },
            ],
        }
    ]
}
