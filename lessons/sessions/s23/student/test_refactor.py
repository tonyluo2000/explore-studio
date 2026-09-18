"""S23 regressions: exact output for the refactor, structure for your system.

The snapshot test passes from the start and must keep passing through every
refactor step. The `my_system` tests fail until you author `my-system.yaml`;
that red bar is the starting line, not a mistake.
"""

import yaml

from lessons.sessions.s23.student.starter import (
    MY_SYSTEM_PATH,
    PLACEHOLDER,
    build_output,
    compose_text,
    load_data,
    pipeline_text,
)


def test_pipeline_output_matches_exact_snapshot():
    expected = (pipeline_text.__globals__["INPUT_PATH"].parent / "expected-output.txt").read_text(
        encoding="utf-8"
    )
    assert pipeline_text() == expected


# TODO: rerun the test above, unchanged, after imports replace monolith helpers.


def test_my_system_has_no_placeholders_left():
    assert PLACEHOLDER not in MY_SYSTEM_PATH.read_text(encoding="utf-8")


def test_my_system_composes_a_shared_style_and_a_responding_keeper():
    """Two mechanics must coexist: one reused toggle style, one keeper reading it."""
    documents = build_output(load_data(MY_SYSTEM_PATH))
    manifest = documents["manifest.yaml"]
    style_ids = {style["id"] for style in manifest["toggle_styles"]}
    lamps = [
        documents[entry["path"]]
        for entry in manifest["contributions"]
        if entry["type"] == "world_object"
    ]
    keepers = [
        documents[entry["path"]]
        for entry in manifest["contributions"]
        if entry["type"] == "character"
    ]

    assert len(style_ids) == 1
    assert len(lamps) == 2
    assert {lamp["toggle_style_id"] for lamp in lamps} == style_ids

    assert len(keepers) == 1
    response = keepers[0]["respond_to_toggle"]
    watched_ids = {
        entry["id"] for entry in manifest["contributions"] if entry["type"] == "world_object"
    }
    assert response["object_id"] in watched_ids
    assert response["when_off"] != response["when_on"]


def test_my_system_choices_are_my_own():
    mine = load_data(MY_SYSTEM_PATH)
    theirs = load_data(MY_SYSTEM_PATH.parent / "workshop-plan.yaml")

    assert mine["keeper"]["when_off"] != theirs["keeper"]["when_off"]
    assert mine["keeper"]["when_on"] != theirs["keeper"]["when_on"]


def test_compose_text_is_valid_yaml_for_every_document():
    for section in compose_text().split("--- ")[1:]:
        header, _, body = section.partition(" ---\n")
        assert header.endswith(".yaml")
        assert isinstance(yaml.safe_load(body), dict)
