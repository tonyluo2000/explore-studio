"""Prepared S25 catalogs. Students should not edit these test fixtures."""

from copy import deepcopy

REQUIRED_IDS = ("summit-flare", "harbor-drum", "north-lantern")

NORMAL_CATALOG = {
    "regions": [
        {
            "name": "Storm Harbor",
            "stations": [
                {
                    "id": "north-lantern",
                    "name": "North Lantern",
                    "enabled": True,
                    "route_order": 2,
                    "signal_power": 4,
                    "world": {
                        "x": 410,
                        "y": 220,
                        "color": "blue",
                        "when_near": "Rain sparks around a steady lantern.",
                        "when_interacted": "The north signal joins the rescue route.",
                    },
                },
                {
                    "id": "harbor-drum",
                    "name": "Harbor Drum",
                    "enabled": True,
                    "route_order": 1,
                    "signal_power": 3,
                    "world": {
                        "x": 210,
                        "y": 330,
                        "color": "orange",
                        "when_near": "A low beat carries through the storm.",
                        "when_interacted": "The harbor signal starts the rescue route.",
                    },
                },
                {
                    "id": "weather-vane",
                    "name": "Weather Vane",
                    "enabled": True,
                    "route_order": 4,
                    "signal_power": 2,
                    "world": {
                        "x": 120,
                        "y": 150,
                        "color": "green",
                        "when_near": "The vane points away from the rescue route.",
                        "when_interacted": "The wind direction is recorded.",
                    },
                },
            ],
        },
        {
            "name": "Lightning Ridge",
            "stations": [
                {
                    "id": "summit-flare",
                    "name": "Summit Flare",
                    "enabled": True,
                    "route_order": 3,
                    "signal_power": 5,
                    "world": {
                        "x": 610,
                        "y": 350,
                        "color": "purple",
                        "when_near": "A violet flare waits above the clouds.",
                        "when_interacted": "The summit signal completes the rescue route.",
                    },
                },
                {
                    "id": "closed-lookout",
                    "name": "Closed Lookout",
                    "enabled": False,
                    "route_order": 5,
                    "signal_power": 8,
                    "world": {
                        "x": 700,
                        "y": 470,
                        "color": "red",
                        "when_near": "The lookout is closed for repairs.",
                        "when_interacted": "No route signal answers.",
                    },
                },
            ],
        },
    ]
}

EXACTLY_THREE_CATALOG = {
    "regions": [
        {
            "name": "Support Route",
            "stations": deepcopy(
                NORMAL_CATALOG["regions"][0]["stations"][:2]
                + NORMAL_CATALOG["regions"][1]["stations"][:1]
            ),
        }
    ]
}

ABSENT_REQUIRED_CATALOG = deepcopy(NORMAL_CATALOG)
ABSENT_REQUIRED_CATALOG["regions"][1]["stations"][0]["id"] = "different-flare"

MALFORMED_COORDINATE_CATALOG = deepcopy(NORMAL_CATALOG)
MALFORMED_COORDINATE_CATALOG["regions"][0]["stations"][0]["world"]["x"] = "410"

STABLE_ORDER_CATALOG = deepcopy(EXACTLY_THREE_CATALOG)
STABLE_ORDER_CATALOG["regions"][0]["stations"][0]["route_order"] = 1
STABLE_ORDER_CATALOG["regions"][0]["stations"][1]["route_order"] = 1
STABLE_ORDER_CATALOG["regions"][0]["stations"][2]["route_order"] = 2
STABLE_REQUIRED_IDS = ("north-lantern", "harbor-drum", "summit-flare")
