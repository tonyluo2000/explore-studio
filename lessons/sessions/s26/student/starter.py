"""S26: runnable, intentionally incomplete capstone blueprint demonstrator."""

try:
    from lessons.sessions.s26.student.project_data import (
        PROJECT_EXPEDITION,
        SPIKE_STATION_IDS,
    )
except ModuleNotFoundError:  # Supports running this file directly.
    from project_data import PROJECT_EXPEDITION, SPIKE_STATION_IDS

REQUIRED_STATION_FIELDS = (
    "id",
    "name",
    "enabled",
    "coordinates",
    "color",
    "route_order",
    "signal_power",
    "story",
)
REQUIRED_STORY_FIELDS = ("when_near", "when_interacted")


def validate_station(station):
    """TODO contract: return a list of errors for one station; never read files."""
    return []


def flatten_stations(expedition):
    """TODO contract: return stations in source order or reject malformed nesting."""
    return []


def validate_expedition(expedition):
    """TODO contract: return all shape/value/duplicate-ID errors; never write files."""
    return []


def select_stations(expedition, required_ids):
    """TODO contract: return enabled matches stably ordered by route_order."""
    return []


def build_package_preview(stations):
    """TODO contract: return current-package object values without writing YAML."""
    return {"objects": []}


def station_ids(stations):
    """Return station IDs in input order; completed support-contract example."""
    return [station["id"] for station in stations]


def main():
    print("S26 blueprint scaffold ready")
    print("Project:", PROJECT_EXPEDITION["name"])
    print("Planned spike IDs:", list(SPIKE_STATION_IDS))
    print("Predict the data flow and failures before completing any TODO function.")


if __name__ == "__main__":
    main()
