"""S27 pure selection, ordering, and aggregation rules; always file-free."""


def find_required(stations, required_ids):
    """TODO: return required records in requested-ID order or fail if absent."""
    return []


def select_enabled(stations):
    """TODO: return enabled records without changing their order."""
    return []


def order_route(stations):
    """TODO: return a stable copy sorted by route_order only."""
    return list(stations)


def signal_total(stations):
    """TODO: return the sum of signal_power values."""
    return 0


def station_ids(stations):
    """Return IDs in input order; completed non-core pure-helper example."""
    return [station["id"] for station in stations]
