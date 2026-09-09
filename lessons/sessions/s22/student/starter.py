"""S22: record one-change repairs with regression assertions."""


def guardian_message(is_on):
    if is_on:
        return "The prism gate is open!"
    return "The prism gate is sleeping."


def first_clue(clues):
    return clues[0]


def main():
    assert first_clue(["switch", "guardian"]) == "switch"
    assert guardian_message(False) == "The prism gate is sleeping."
    assert guardian_message(True) == "The prism gate is open!"
    print("3 regression checks pass")
    # TODO: add one assertion protecting the exact clue count after a repair.


if __name__ == "__main__":
    main()
