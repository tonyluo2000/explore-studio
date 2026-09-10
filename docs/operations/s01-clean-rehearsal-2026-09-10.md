# S01 Clean Student-Flow Rehearsal — 2026-09-10

> **Result:** Pass on macOS using a fresh student checkout and virtual
> environment. The same test is required on pull requests by the Student
> template integration workflow.

## Rehearsal inputs

- student template repository: `tonyluo2000/student-adventure-template`;
- exact template commit: `22afcc5c6f4f24ffd7e67d8ff70b0f8d49f5ff38`;
- course-material candidate: `codex/pre-class-readiness` on 2026-09-10;
- exact installed Explore Studio platform commit:
  `308bc6c0a2b149e8058f46c8f1beece50b793969`; and
- test host: macOS, Python 3.13.7, isolated temporary checkout and `.venv`.

The platform commit was published and independently resolved from the remote
branch before the rehearsal. The temporary student checkout began at the exact
pinned template tree; it did not reuse this repository's virtual environment or
Python import path.

## Student flow exercised

1. Fetched and detached the exact template commit into a new temporary Git
   repository.
2. Provisioned the student-only overlay with
   `scripts/provision_student_workspace.py`.
3. Confirmed 30 student task cards, no teacher runbooks, no S31 directory, and
   no copied `explore/` or `engine/` source.
4. Created a new virtual environment and installed
   `requirements-course.txt`.
5. Confirmed the installed `explore` module came from that environment and the
   `explore-package` command opened its help.
6. Ran the template test suite and validated the template package.
7. Ran `lessons/sessions/s01/student/starter.py` and received the three expected
   classroom-object lines.
8. Validated the `nova-character`, `forest-guide`, `crystal-lantern`, and
   `river-fountain` example packages.
9. Launched the real S01 `explore-package trail` flow with
   `--mission-id visit-all-classroom-objects` under SDL's headless drivers,
   posted a window-close event, and confirmed a clean zero exit.
10. Exported the template package and confirmed the archive was created.

## Outcome and boundary

The automated rehearsal passed (`1 passed in 16.14s`). It exercises the real
derived student repository, exact dependency installation, console script, S01
starter, example packages, and Trail runtime—not imports from the Explore
Studio working checkout.

This was a synthetic pre-class rehearsal. It used no student credentials or
personal data, and it did not test native Windows. Classroom Windows devices
must complete the separate WSL 2/WSLg device check in
[`classroom-student-workspace.md`](../classroom-student-workspace.md).
