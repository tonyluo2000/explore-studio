"""S27 data access and flattening; no validation policy or file writing."""

try:
    from lessons.sessions.s27.student.project_data import PROJECT_PLAN
except ModuleNotFoundError:  # Supports direct execution from this directory.
    from project_data import PROJECT_PLAN


def get_project_plan():
    """Return the student-owned in-memory plan."""
    return PROJECT_PLAN


def flatten_stations(plan):
    """TODO: return station dictionaries in zone/source order."""
    return []
