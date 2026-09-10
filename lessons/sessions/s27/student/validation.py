"""S27 deterministic validation with no file I/O."""

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


def validate_plan(plan):
    """TODO: return ordered fail-closed diagnostics; an empty list means valid."""
    return []
