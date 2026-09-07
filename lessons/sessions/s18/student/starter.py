"""S18: summarize local power-station counter records."""

counters = [
    {"id": "wind-core", "count": 2, "goal": 3},
    {"id": "sun-core", "count": 4, "goal": 4},
    {"id": "tide-core", "count": 4, "goal": 5},
]


def summarize_counts(records):
    if not records:
        return None

    counts = []
    for record in records:
        counts.append(record["count"])

    # TODO: replace the placeholder numbers with min, max, sum, and average.
    return {"minimum": 0, "maximum": 0, "total": 0, "average": 0.0}


def at_goal(count, goal):
    # TODO: return the boundary comparison from S10.
    return False


print(summarize_counts(counters))
print(summarize_counts([]))
print(at_goal(2, 3), at_goal(3, 3), at_goal(4, 3))
