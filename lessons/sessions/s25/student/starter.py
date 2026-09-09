"""S25: complete one tested catalog-to-playable-preview pipeline."""

try:
    from lessons.sessions.s25.student.fixtures import NORMAL_CATALOG, REQUIRED_IDS
except ModuleNotFoundError:  # Supports running this file directly.
    from fixtures import NORMAL_CATALOG, REQUIRED_IDS

REQUIRED_STATION_FIELDS = (
    "id",
    "name",
    "enabled",
    "route_order",
    "signal_power",
    "world",
)
REQUIRED_WORLD_FIELDS = ("x", "y", "color", "when_near", "when_interacted")


def catalog_stations(catalog):
    """Flatten the prepared regions without changing station order."""
    stations = []
    for region in catalog["regions"]:
        for station in region["stations"]:
            stations.append(station)
    return stations


def validate_station(station):
    """Return errors for the prepared station shape; an empty list means valid."""
    errors = []
    # TODO: validate the station/world dictionaries, required fields, field
    # types, nonnegative power, positive route order, and x/y from 40 to 760.
    return errors


def select_route(catalog, required_ids):
    """Return exactly three enabled required stations in requested-ID order."""
    selected = []
    # TODO: filter enabled stations, search once for each required ID, fail on
    # an absent ID, then require exactly three selected records.
    return selected


def signal_total(stations):
    """Return the sum of signal_power for the selected stations."""
    # TODO: aggregate signal_power with a readable loop.
    return 0


def ordered_route(stations):
    """Return a stable sorted copy using route_order only."""
    # TODO: use sorted(..., key=...); do not add an ID tie-breaker.
    return list(stations)


def transform_preview(stations):
    """Transform reviewed route records into current-contract preview values."""
    objects = []
    for station in stations:
        world = station["world"]
        objects.append(
            {
                "id": station["id"],
                "name": station["name"],
                "x": world["x"],
                "y": world["y"],
                "color": world["color"],
                "when_near": world["when_near"],
                "when_interacted": world["when_interacted"],
            }
        )
    return {"route_ids": [station["id"] for station in stations], "objects": objects}


def build_preview(catalog, required_ids):
    """Run validation through transformation, failing before preview on bad data."""
    stations = catalog_stations(catalog)
    errors = []
    for number, station in enumerate(stations, start=1):
        for error in validate_station(station):
            errors.append(f"station {number}: {error}")
    if errors:
        raise ValueError("invalid station data: " + "; ".join(errors))

    selected = select_route(catalog, required_ids)
    if len(selected) != 3:
        raise ValueError("exactly three required stations must be selected")
    ordered = ordered_route(selected)
    return {
        "selected_count": len(selected),
        "signal_power": signal_total(selected),
        "preview": transform_preview(ordered),
    }


def main():
    print("S25 scaffold ready")
    print("Catalog stations:", len(catalog_stations(NORMAL_CATALOG)))
    print("Required route count:", len(REQUIRED_IDS))
    print("Record all four predictions, then complete the TODO functions.")


if __name__ == "__main__":
    main()
