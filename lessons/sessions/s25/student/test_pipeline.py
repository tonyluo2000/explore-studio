"""Five focused S25 tests. They become green as the four TODO functions are completed."""

import pytest

from lessons.sessions.s25.student import starter
from lessons.sessions.s25.student.fixtures import (
    ABSENT_REQUIRED_CATALOG,
    EXACTLY_THREE_CATALOG,
    MALFORMED_COORDINATE_CATALOG,
    NORMAL_CATALOG,
    REQUIRED_IDS,
    STABLE_ORDER_CATALOG,
    STABLE_REQUIRED_IDS,
)


def test_normal_valid_catalog():
    result = starter.build_preview(NORMAL_CATALOG, REQUIRED_IDS)

    assert result["selected_count"] == 3
    assert result["signal_power"] == 12
    assert result["preview"]["route_ids"] == [
        "harbor-drum",
        "north-lantern",
        "summit-flare",
    ]
    assert len(result["preview"]["objects"]) == 3


def test_exactly_three_boundary():
    result = starter.build_preview(EXACTLY_THREE_CATALOG, REQUIRED_IDS)

    assert result["selected_count"] == 3


def test_absent_required_id_fails_closed_before_preview(monkeypatch):
    preview_called = False

    def unexpected_preview(stations):
        nonlocal preview_called
        preview_called = True
        return {"route_ids": [], "objects": []}

    monkeypatch.setattr(starter, "transform_preview", unexpected_preview)
    with pytest.raises(ValueError, match="summit-flare"):
        starter.build_preview(ABSENT_REQUIRED_CATALOG, REQUIRED_IDS)

    assert not preview_called


def test_malformed_coordinate_type_fails_closed_before_preview(monkeypatch):
    preview_called = False

    def unexpected_preview(stations):
        nonlocal preview_called
        preview_called = True
        return {"route_ids": [], "objects": []}

    monkeypatch.setattr(starter, "transform_preview", unexpected_preview)
    with pytest.raises(ValueError, match="x must be an integer"):
        starter.build_preview(MALFORMED_COORDINATE_CATALOG, REQUIRED_IDS)

    assert not preview_called


def test_stable_order_regression():
    selected = starter.select_route(STABLE_ORDER_CATALOG, STABLE_REQUIRED_IDS)
    ordered = starter.ordered_route(selected)

    assert [station["id"] for station in ordered] == [
        "north-lantern",
        "harbor-drum",
        "summit-flare",
    ]
