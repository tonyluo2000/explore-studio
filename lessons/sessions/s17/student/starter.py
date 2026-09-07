"""S17: find, filter, and count clue records."""

clues = [
    {"id": "ember-note", "name": "Ember Note", "color": "orange"},
    {"id": "river-mark", "name": "River Mark", "color": "blue"},
    {"id": "sky-thread", "name": "Sky Thread", "color": "blue"},
    {"id": "moss-arrow", "name": "Moss Arrow", "color": "green"},
]


def find_by_id(records, target_id):
    # TODO: return the matching record, or None when no ID matches.
    return None


def filter_by_color(records, target_color):
    # TODO: return matching records in their original order.
    return []


def count_matching(records, key, expected_value):
    # TODO: count records whose selected key has the expected value.
    return 0


print(find_by_id(clues, "river-mark"))
print(filter_by_color(clues, "blue"))
print(count_matching(clues, "color", "blue"))
