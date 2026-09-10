"""S27 thin runner for the intentionally incomplete modular capstone core."""

try:
    from lessons.sessions.s27.student import builder, data_io, rules, validation
except ModuleNotFoundError:  # Supports running this file directly.
    import builder
    import data_io
    import rules
    import validation


def main():
    plan = data_io.get_project_plan()
    print("S27 modular core scaffold ready")
    print("Project:", plan["name"])
    print("Modules: data_io → validation → rules → builder")
    print(
        "Imported helpers:",
        validation.validate_plan.__name__,
        rules.find_required.__name__,
        builder.build_documents.__name__,
    )
    print("Record intermediate shapes before completing TODO helpers.")


if __name__ == "__main__":
    main()
