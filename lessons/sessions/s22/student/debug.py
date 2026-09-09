"""S22 prepared failures: repair and rerun one scenario at a time."""


def key_error_case():
    guardian = {"name": "Prism Guardian", "color": "blue"}
    return guardian["message"]  # KeyError: the authored key is missing.


def off_by_one_case():
    clues = ["switch", "guardian"]
    return clues[len(clues)]  # IndexError: last valid index is len(clues) - 1.


def incorrect_return_case(is_on):
    if is_on:
        return "The prism gate is sleeping."  # Wrong branch result.
    return "The prism gate is open!"


def run_prepared_failure(case_name):
    if case_name == "key-error":
        return key_error_case()
    if case_name == "off-by-one":
        return off_by_one_case()
    if case_name == "incorrect-return":
        assert incorrect_return_case(True) == "The prism gate is open!"
        return None
    raise ValueError(f"unknown prepared case: {case_name}")


if __name__ == "__main__":
    # TODO: change only this selected case after completing its traceback receipt.
    run_prepared_failure("key-error")
