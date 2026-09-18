"""S22: record one-change repairs with regression assertions."""

CLUES = ("switch", "guardian", "prism")


def guardian_message(is_on):
    if is_on:
        return "The prism gate is open!"
    return "The prism gate is sleeping."


def first_clue(clues):
    return clues[0]


def clue_count(clues):
    """Report how many clues the guardian is holding."""
    return len(clues) - 1


def main():
    assert first_clue(["switch", "guardian"]) == "switch"
    assert guardian_message(False) == "The prism gate is sleeping."
    assert guardian_message(True) == "The prism gate is open!"
    print("3 regression checks pass")
    print("clues:", clue_count(CLUES), "of", CLUES)
    # TODO: the printed clue count disagrees with CLUES. Write the assertion that
    # catches it, watch it fail, then make exactly one change so it passes.


if __name__ == "__main__":
    main()
