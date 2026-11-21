# Course Kit classroom release gate

A runtime-changing lecture is NOT complete after the implementation PR merges.
Website Slides/Learn/Journey publication describes website availability only.

The ordered release states are BUILDING → REVIEWED → MERGED →
COURSE_KIT_PUBLISHED → LIVE_VERIFIED → CLASSROOM_VERIFIED. REVIEWED requires an
independent review of the exact implementation head. MERGED is implementation
availability, not classroom readiness. COURSE_KIT_PUBLISHED means repository ZIP
bytes match the contract after a separately approved publication merge.
LIVE_VERIFIED requires downloading matching production bytes. CLASSROOM_VERIFIED
additionally requires isolated fresh install and live-kit S06–S09 Trail acceptance.
Never infer live state from Git or website deployment.

## Owner workflow

1. Prepare the lesson; commit approved runtime changes, update all existing
   runtime pins and commit lesson source. Use a clean checkout. Run
   `python scripts/prepare_course_release.py --session S09` (use current session).
   This double-builds a candidate, validates provenance, writes the canonical
   contract, and saves a receipt, ZIP, publication PR body and exact commands in
   ignored `build/course-releases/<source-head>/`. Commit the generated contract
   in the implementation PR. Preserve the bundle or download the CI artifact.
2. Obtain independent exact-head implementation review. Run all readiness checks.
3. Merge implementation only with owner approval: **IMPLEMENTATION MERGED**.
   Main's freshness gate will intentionally be red while the production kit lags.
4. Follow `publication.json` from the bundle to prepare the ZIP-only publication
   branch/PR. The publication helper validates before writing and refuses dirty
   source, unrelated changes, stale source, wrong SHA/runtime/provenance/inventory.
   Candidate preparation and CI never open, merge or deploy a publication PR.
5. Obtain independent exact-head publication review and owner merge approval.
   Merge the publication PR: **COURSE KIT PUBLISHED**. Main must now pass.
6. After the separately authorized deployment, run
   `python scripts/verify_live_course_release.py --session S09`:
   **LIVE VERIFIED** only on matching actual downloaded bytes.
7. Run `python scripts/verify_live_course_release.py --session S09 --install-smoke-test`.
   This downloads again, installs requirements in a new temporary venv/home,
   runs the shipped `check-my-computer.py`, and drives all S06–S09 canonical
   Trails using installed runtime and extracted kit packages.
8. Preserve the successful command output as dated review evidence:
   **CLASSROOM VERIFIED**. A failure or later contract change revokes readiness.
   Visual review remains a separate review requirement; headless acceptance
   establishes presentation activation and deterministic behavior, not aesthetics.

## One source of truth

`docs/operations/course-release.json` records the expected artifact, immutable
materials/runtime commits, implementation source head, session and exact member
inventory. It is internal; no student page or command changes. It stores no
mutable readiness flags. Publication head is derived from Git history for the
ZIP rather than embedded in itself (which would require a self-referential SHA).
Live/classroom certification additionally requires the identical contract and ZIP
on fetched `origin/main`; fetch main before verification. Unmerged matching bytes
are reported as candidate evidence and cannot certify classroom readiness.
Live/classroom states are outputs of fresh verification, never hand-edited JSON
or a previously saved receipt. Offline status conservatively reports readiness
BLOCKED and live SHA unverified even if someone previously ran verification.

`python scripts/course_release_status.py` is strict by default. It validates
contract schema, current calendar publication, runtime pin, source ancestry,
current shipped material equality, runtime tree equality, double rebuild,
SHA256, member count/inventory and embedded provenance. A structurally valid
older ZIP fails with PRODUCTION_COURSE_KIT_STALE.

PR CI classifies by its actual base/head diff, never a label or caller-selected
phase. No ZIP change means implementation: a validated candidate can coexist
with explicitly reported production lag. A ZIP change means publication: only
the ZIP may change and it must close the lag. Main and manual readiness are
always strict. Every PR and main push runs readiness so changes to new source
paths cannot bypass the gate. Existing provenance/readiness checks remain.

The live verifier uses unique query parameters and no-cache request headers,
compares actual bytes, and reports response cache headers. A stale response is
LIVE_COURSE_KIT_STALE. No saved state or merged ZIP can bypass this check.

## Safety and migration

The public download URL, standalone ZIP format, Windows/WSL instructions,
`check-my-computer.py`, lesson commands, Journey tooling and deterministic
builder remain unchanged. Runtime changes must be pinned to a committed runtime
before building. Newly published polished lessons beyond S09 must add acceptance
before classroom certification; the live verifier fails closed for unsupported
sessions. The original S09 failure (253-member runtime d1e89a1d versus required
runtime a01c8a6f, 294 members) is the initial migration's blocked main status;
this policy PR intentionally does not publish that ZIP. The separately reviewed
publication candidate can close the lag without changing the contract.

Release tools never target either the installed `~/explore-studio-course` or
student-owned `~/my-explore-world`. Only the fixed repository public ZIP can be
replaced; installations and Trail runs happen in disposable temp directories.
Receipts use SHAs and repo-relative paths, never local home paths or credentials.
