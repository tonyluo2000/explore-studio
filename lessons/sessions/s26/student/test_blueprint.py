"""Focused S26 tests. Complete the TODO contracts to make this file green."""

import pytest

from lessons.sessions.s26.student import starter
from lessons.sessions.s26.student.fixtures import (
    ABSENT_REQUIRED_ID_EXPEDITION,
    DUPLICATE_STATION_ID_EXPEDITION,
    MALFORMED_NESTED_EXPEDITION,
    MINIMAL_VALID_EXPEDITION,
    STABLE_REQUIRED_IDS,
    STABLE_SELECTION_EXPEDITION,
    VALID_STATION,
)


def test_valid_station_has_no_errors():
    assert starter.validate_station(VALID_STATION) == []


def test_absent_required_id_fails_selection():
    with pytest.raises(ValueError, match="absent-station"):
        starter.select_stations(ABSENT_REQUIRED_ID_EXPEDITION, ("absent-station",))


def test_malformed_nested_shape_is_rejected():
    errors = starter.validate_expedition(MALFORMED_NESTED_EXPEDITION)

    assert errors
    assert any("zones" in error for error in errors)


def test_duplicate_station_id_is_rejected():
    errors = starter.validate_expedition(DUPLICATE_STATION_ID_EXPEDITION)

    assert any("duplicate station id: harbor-beacon" in error for error in errors)


def test_selection_order_is_deterministic_and_stable():
    selected = starter.select_stations(STABLE_SELECTION_EXPEDITION, STABLE_REQUIRED_IDS)

    assert starter.station_ids(selected) == [
        "north-light",
        "harbor-beacon",
        "summit-flare",
    ]


def test_acceptance_one_selected_station_becomes_one_package_object():
    selected = starter.select_stations(MINIMAL_VALID_EXPEDITION, ("harbor-beacon",))
    preview = starter.build_package_preview(selected)

    assert preview == {
        "objects": [
            {
                "id": "harbor-beacon",
                "name": "Harbor Beacon",
                "x": 220,
                "y": 320,
                "color": "orange",
                "when_near": "The harbor beacon flickers through the rain.",
                "when_interacted": "You focus the beacon across the water.",
            }
        ]
    }
