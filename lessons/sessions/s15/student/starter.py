"""S15: validate and trace a three-object secret sequence."""


def has_three_distinct_ids(object_ids):
    # TODO: length alone does not reject a repeated ID.
    return len(object_ids) == 3


def next_progress(expected_ids, progress, attempted_id):
    """Apply the Trail's fixed sequence rule to one interaction."""
    if progress == len(expected_ids):
        return progress
    if attempted_id == expected_ids[progress]:
        return progress + 1
    if attempted_id in expected_ids:
        return 0
    return progress


def compare_order(expected_ids, attempted_ids):
    progress = 0
    for attempted_id in attempted_ids:
        # TODO: replace this placeholder block with one next_progress call.
        if attempted_id:
            pass
    return progress


expected = ["star-map", "moon-switch", "echo-drum"]

# TODO: write a normal-case assertion showing expected order reaches 3.
# TODO: add an assertion showing that star-map then echo-drum resets to zero.
print(has_three_distinct_ids(expected))
print(compare_order(expected, expected))
print(compare_order(expected, ["star-map", "echo-drum"]))
print(compare_order(expected, ["star-map", "crystal-lantern"]))
