# Class-World Package Artifact File Verification v0.1

> **Status:** Implemented bounded read-only binding of explicit package
> artifact files to one successful assembly-input plan, with content digest
> verification delegated unchanged to the existing pure verifier.
> Materialization, archive parsing, execution, signing, approval, publication,
> and deployment remain deferred.

Artifact File Verification v0.1 answers one narrow question:

> Can this exact set of explicitly bound local files be read safely inside one
> artifact root and, if so, do their bytes match the planned package artifact
> identities?

```text
successful ClassWorldAssemblyPlanResult
        +
absolute artifact root directory
        +
immutable explicit package/version/relative-path bindings
        ↓
validate one-to-one identities and canonical paths
        ↓
resolve and inspect every file inside the root
        ↓
bounded read in canonical plan order
        ↓
existing verify_class_world_artifact_contents
        ↓
immutable file-read metadata + unchanged content-verification result
```

## Scope and architecture position

This is the first filesystem boundary after pure artifact-content verification.
It adds only explicit binding, root confinement, bounded reads, and composition
with the existing verifier.

It does not hash bytes itself. It does not rebuild or recompute the assembly
plan, inventory, release declaration, or expected artifact identities. It does
not parse or extract package files, infer archive formats, validate package
contents, or load Explorer Packages.

Package artifact files are opaque bytes at this boundary. A digest match says
nothing about their format or safety for later parsing.

## Public API

```python
from explore.packages import (
    ClassWorldPackageArtifactFileBinding,
    verify_class_world_artifact_files,
)

result = verify_class_world_artifact_files(
    assembly_plan_result,
    "/absolute/artifact-root",
    (
        ClassWorldPackageArtifactFileBinding(
            package_id="alice-fox",
            package_version="1.2.0",
            relative_path="packages/alice-fox-1.2.0.pkg",
        ),
    ),
)
```

The public contract includes:

- `verify_class_world_artifact_files`;
- `ClassWorldPackageArtifactFileBinding` and
  `ClassWorldPackageArtifactFileRead`;
- `ClassWorldArtifactFileVerificationResult`;
- `ClassWorldArtifactFileVerificationIssue` and its stable issue-code enum;
- `SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION`;
- `MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES`; and
- `MAX_CLASS_WORLD_ARTIFACT_SET_BYTES`.

The contract version is `"0.1"`. The per-file limit is 67,108,864 bytes
(64 MiB), and the aggregate payload limit is 268,435,456 bytes (256 MiB).

## Upstream and validation precedence

The upstream input must be the exact existing `ClassWorldAssemblyPlanResult`
type and contain one usable plan and no issues. Missing, wrong-type, failed, or
malformed upstream state fails before root or binding inspection.

The operation then validates, in order:

1. root value type and absolute-path requirement;
2. immutable binding tuple, exact binding types, identities, versions, and path
   syntax;
3. root filesystem state;
4. every bound file's containment, type, identity, and declared size;
5. bounded file reads; and
6. delegated content verification.

Structural failures therefore do not trigger filesystem reads. Filesystem
failures do not invoke content verification.

## Explicit and unambiguous binding

Each binding names an exact package ID, exact package version, and artifact-root
relative path. The bindings may be supplied in any order, but successful reads
and delegated bytes always follow the canonical package order already retained
by the assembly plan.

Bindings must form a one-to-one mapping:

- every planned package appears exactly once;
- unplanned packages are rejected;
- binding versions equal their planned versions;
- one package cannot appear twice;
- one canonical relative path cannot be assigned twice; and
- distinct paths resolving to the same device/inode identity are rejected.

The last rule rejects hard-link and case-alias ambiguity where the host
filesystem exposes both names as the same file identity.

Any binding issue makes the result atomic: no files or content-verification
state are returned. Diagnostics follow caller binding order, followed by missing
packages in canonical plan order.

## Root confinement and path rules

`artifact_root` must be an explicit absolute `str` or `pathlib.Path`, exist as a
directory, and not itself be a symbolic link. It is resolved once as the
containment anchor.

Binding paths must be exact canonical portable strings using forward slashes.
The layer rejects:

- empty, whitespace-only, non-string, or `.` paths;
- absolute POSIX, Windows drive, or UNC paths;
- backslashes and NUL characters;
- `..` traversal;
- redundant `.`, repeated separators, or other noncanonical spellings;
- any symbolic link at the final path or an intermediate component; and
- any resolved target outside the root.

Every target must exist as a regular file. Diagnostics contain only structural
binding locations and package IDs, never absolute host paths.

## Bounded read behavior

All targets are inspected before any is read. Oversized files and aggregate
declared size fail before opening files. Each opened descriptor is checked
again for regular-file type, stable device/inode identity, and size.

Each stream reads at most the per-file limit plus one byte, so growth after
inspection remains bounded and detectable. Aggregate bytes are checked again
while reading. A failure returns no partial file metadata or payload tuple.

The layer retains no artifact bytes in its result. Successful file metadata
contains only the exact canonical binding and byte count.

## Delegated verification

After every file is read successfully, the immutable byte tuple is passed once
to `verify_class_world_artifact_contents`. Its result is retained unchanged.
This layer imports no hashing library and defines no digest comparison logic.

A digest mismatch is therefore normal completed content-verification state:
file reading can be complete while aggregate `all_match` is false. Transport or
binding issues remain distinct from digest mismatch.

## Trust and safety boundary

A successful result proves only that the explicitly bound files were read
inside the supplied root and their read bytes were delegated to the declared
digest verifier. It does not establish artifact provenance, archive safety,
authenticity, approval, publication status, or authority.

The operation performs no writes, extraction, parsing, package validation,
package loading, student-code execution, runtime registration, network,
database, Git, environment, clock, randomness, Pygame, authentication, signing,
approval, publication, or deployment work.

Later contracts may define deterministic output layout and materialization,
safe archive parsing, assembled-output hashing, attribution output, signing or
attestation, approval, publication, and deployment.
