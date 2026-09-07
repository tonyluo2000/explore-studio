"""S12: allow either signal with Boolean or."""


def either_signal(river_on, hill_on):
    # TODO: this copied AND rule is too strict for an either-signal rescue.
    return river_on and hill_on


cases = [
    (False, False),
    (False, True),
    (True, False),
    (True, True),
]

for river_on, hill_on in cases:
    print(river_on, hill_on, either_signal(river_on, hill_on))
