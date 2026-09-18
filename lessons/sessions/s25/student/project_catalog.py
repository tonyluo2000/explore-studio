"""My editable S25 project source: the three stops of my own route.

This is the Milestone B project catalog. Nothing here names a premise yet —
that decision is mine. Replace every ``CHOOSE-ME``, then make the same reviewed
changes in ``explorer-package/``.

The three station ``id`` values are scaffolding: they already match the object
file names, the manifest, and the keeper's ``respond_to_sequence`` list, so I
can rename the *story* without rewiring the package. Renaming IDs is an
optional extension, not part of the milestone.

Safe bounds:

* keep exactly three stations for the core route;
* keep names and messages nonempty and in my own words;
* keep ``x`` and ``y`` integers from 40 through 760;
* keep ``signal_power`` at zero or greater;
* keep ``route_order`` values positive and use 1, 2, and 3 for a clear route;
* use supported color names already seen in the lesson examples.
"""

PROJECT_ROUTE_IDS = ("first-stop", "second-stop", "third-stop")

#: Milestone B needs TWO supported mechanics in one prototype. The M15 ordered
#: route is mechanic one. This block records mechanic two *before* I author it.
#:
#: * ``kind`` — one of "counter", "toggle", "two_toggles", "either_toggle".
#: * ``object_id`` — which object carries it. A route ID above means one player
#:   action feeds both mechanics; a fourth, non-route object keeps them apart.
#: * ``relationship`` — one sentence: how does mechanic two change what the
#:   player understands about the route?
#:
#: This block is local planning data. It is *not* copied into package YAML; the
#: package says the same thing in the runtime's own fields.
SECOND_MECHANIC = {
    "kind": "CHOOSE-ME",
    "object_id": "CHOOSE-ME",
    "relationship": "CHOOSE-ME",
}

PROJECT_CATALOG = {
    "regions": [
        {
            "name": "CHOOSE-ME",
            "stations": [
                {
                    "id": "first-stop",
                    "name": "CHOOSE-ME",
                    "enabled": True,
                    "route_order": 1,
                    "signal_power": 2,
                    "world": {
                        "x": 180,
                        "y": 310,
                        "color": "green",
                        "when_near": "CHOOSE-ME",
                        "when_interacted": "CHOOSE-ME",
                    },
                },
                {
                    "id": "second-stop",
                    "name": "CHOOSE-ME",
                    "enabled": True,
                    "route_order": 2,
                    "signal_power": 3,
                    "world": {
                        "x": 390,
                        "y": 230,
                        "color": "blue",
                        "when_near": "CHOOSE-ME",
                        "when_interacted": "CHOOSE-ME",
                    },
                },
                {
                    "id": "third-stop",
                    "name": "CHOOSE-ME",
                    "enabled": True,
                    "route_order": 3,
                    "signal_power": 4,
                    "world": {
                        "x": 610,
                        "y": 350,
                        "color": "purple",
                        "when_near": "CHOOSE-ME",
                        "when_interacted": "CHOOSE-ME",
                    },
                },
            ],
        }
    ]
}
