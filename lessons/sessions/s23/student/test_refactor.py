"""S23 exact-output regression to run before and after refactoring."""

from lessons.sessions.s23.student.starter import pipeline_text


def test_pipeline_output_matches_exact_snapshot():
    expected = (pipeline_text.__globals__["INPUT_PATH"].parent / "expected-output.txt").read_text(
        encoding="utf-8"
    )
    assert pipeline_text() == expected


# TODO: rerun this unchanged test after imports replace monolith helpers.
