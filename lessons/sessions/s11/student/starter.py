"""S11: require both keys with Boolean and."""


def both_keys(first_on, second_on):
    # TODO: repair this so only the both-True case returns True.
    return first_on


cases = [
    (False, False),
    (False, True),
    (True, False),
    (True, True),
]

for first_on, second_on in cases:
    print(first_on, second_on, both_keys(first_on, second_on))
