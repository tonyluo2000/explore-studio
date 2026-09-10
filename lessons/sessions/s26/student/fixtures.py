"""Fixed S26 nested-data fixtures. Students should not edit this file."""

from copy import deepcopy

VALID_STATION = {
    "id": "harbor-beacon",
    "name": "Harbor Beacon",
    "enabled": True,
    "coordinates": {"x": 220, "y": 320},
    "color": "orange",
    "route_order": 1,
    "signal_power": 3,
    "story": {
        "when_near": "The harbor beacon flickers through the rain.",
        "when_interacted": "You focus the beacon across the water.",
    },
}

MINIMAL_VALID_EXPEDITION = {
    "name": "Stormlight Rescue Trail",
    "zones": [{"id": "harbor", "name": "Harbor", "stations": [deepcopy(VALID_STATION)]}],
}

ABSENT_REQUIRED_ID_EXPEDITION = deepcopy(MINIMAL_VALID_EXPEDITION)

MALFORMED_NESTED_EXPEDITION = {
    "name": "Broken Trail",
    "zones": {"id": "not-a-list", "stations": []},
}

DUPLICATE_STATION_ID_EXPEDITION = deepcopy(MINIMAL_VALID_EXPEDITION)
DUPLICATE_STATION_ID_EXPEDITION["zones"].append(
    {
        "id": "ridge",
        "name": "Ridge",
        "stations": [deepcopy(VALID_STATION)],
    }
)

STABLE_SELECTION_EXPEDITION = deepcopy(MINIMAL_VALID_EXPEDITION)
STABLE_SELECTION_EXPEDITION["zones"][0]["stations"] = [
    {
        **deepcopy(VALID_STATION),
        "id": "north-light",
        "name": "North Light",
        "route_order": 1,
    },
    {
        **deepcopy(VALID_STATION),
        "id": "harbor-beacon",
        "route_order": 1,
    },
    {
        **deepcopy(VALID_STATION),
        "id": "summit-flare",
        "name": "Summit Flare",
        "route_order": 2,
    },
]
STABLE_REQUIRED_IDS = ("north-light", "harbor-beacon", "summit-flare")
