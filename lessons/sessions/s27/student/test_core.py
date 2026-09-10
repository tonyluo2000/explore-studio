"""Focused S27 learner tests for the accepted modular-core contracts."""

import pytest

from lessons.sessions.s27.student import builder, data_io, rules, validation
from lessons.sessions.s27.student.fixtures import (
    ACCEPTED_S26_PLAN,
    DUPLICATE_ID_PLAN,
    EMPTY_ZONE_PLAN,
    EXPECTED_DOCUMENTS,
    MISSING_REQUIRED_STATION_PLAN,
    STABLE_ORDER_TIE_PLAN,
    WRONG_TYPE_RECORD_PLAN,
)


def test_accepted_s26_plan_has_no_diagnostics():
    assert validation.validate_plan(ACCEPTED_S26_PLAN) == []


def test_empty_zone_flattens_to_empty_list():
    assert data_io.flatten_stations(EMPTY_ZONE_PLAN) == []


def test_missing_required_station_fails_closed():
    stations = data_io.flatten_stations(MISSING_REQUIRED_STATION_PLAN)

    with pytest.raises(ValueError, match="absent-station"):
        rules.find_required(stations, MISSING_REQUIRED_STATION_PLAN["required_station_ids"])


def test_wrong_type_record_has_deterministic_diagnostic():
    assert validation.validate_plan(WRONG_TYPE_RECORD_PLAN) == [
        "zones[0].stations[0].route_order must be a positive integer"
    ]


def test_duplicate_id_fails_closed_after_record_checks():
    assert validation.validate_plan(DUPLICATE_ID_PLAN) == ["duplicate station id: harbor-beacon"]


def test_find_filter_and_order_preserve_stable_tie():
    stations = data_io.flatten_stations(STABLE_ORDER_TIE_PLAN)
    found = rules.find_required(stations, STABLE_ORDER_TIE_PLAN["required_station_ids"])
    enabled = rules.select_enabled(found)
    ordered = rules.order_route(enabled)

    assert rules.station_ids(ordered) == [
        "north-lantern",
        "harbor-beacon",
        "summit-flare",
    ]


def test_signal_total_aggregates_selected_records():
    stations = data_io.flatten_stations(ACCEPTED_S26_PLAN)
    found = rules.find_required(stations, ACCEPTED_S26_PLAN["required_station_ids"])

    assert rules.signal_total(rules.select_enabled(found)) == 9


def test_build_documents_matches_exact_deterministic_output():
    stations = data_io.flatten_stations(ACCEPTED_S26_PLAN)
    found = rules.find_required(stations, ACCEPTED_S26_PLAN["required_station_ids"])
    ordered = rules.order_route(rules.select_enabled(found))

    assert builder.build_documents(ACCEPTED_S26_PLAN, ordered) == EXPECTED_DOCUMENTS
