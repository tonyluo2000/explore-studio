"""S13: turn one rule around with Boolean not."""


def moonflower_awake(is_on):
    # TODO: this returns the original value, like the mistaken idea that two
    # inversions would make the result "more opposite."
    return is_on


print(False, moonflower_awake(False))
print(True, moonflower_awake(True))
