# Verified Class-World Package Artifact Materialization v0.1

> **Status:** Implemented bounded source reverification and atomic publication
> of the exact verified package byte tuple to one plan-authorized output tree.
> Archive parsing or extraction, package loading, execution, signing, approval,
> publication to external systems, and deployment remain deferred.

Verified Materialization v0.1 answers one narrow question:

> Can the package artifact sources named by this successful materialization
> plan be safely read and reverified now, and can those exact verified bytes be
> atomically placed at only the plan-authorized output paths?

```text
successful ClassWorldMaterializationPlanResult
        +
explicit absolute artifact root
        +
explicit absent output root with existing parent
        ↓
rebuild and compare the pure layout plan
        ↓
existing artifact-file pipeline with descriptor-confined source traversal
        ↓
existing content verifier receives one bounded byte tuple
        ↓
same byte tuple is written to private sibling staging
        ↓
atomic directory replacement into the authorized output root
        ↓
immutable ClassWorldVerifiedMaterializationResult
```

## Scope and architecture position

This is the smallest filesystem materialization primitive after deterministic
layout planning. It consumes the existing plan contract, reuses the existing
file-verification pipeline and content verifier, and adds only destination
confinement, bounded writes, private staging, and atomic publication of a new
output tree.

It does not interpret package artifact bytes. Every source remains one opaque,
independent Explorer Package artifact and every destination remains inside its
plan-assigned package ID and version directory.

## Public API

```python
from explore.packages import materialize_verified_class_world_artifacts

result = materialize_verified_class_world_artifacts(
    materialization_plan_result,
    "/absolute/artifact-root",
    "/absolute/output-parent/new-release",
)
```

The public contract includes:

- `materialize_verified_class_world_artifacts`;
- `ClassWorldMaterializedPackage`;
- `ClassWorldVerifiedMaterialization` and its result model;
- `ClassWorldVerifiedMaterializationIssue` and its stable issue-code enum; and
- `SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION`.

The contract version is `"0.1"`.

## Plan authority and validation precedence

The input must be the exact existing materialization-plan result type with one
successful plan and no issues. The materializer passes the plan's retained file
verification back through the existing pure plan builder and requires the
rebuilt plan to equal the supplied plan. This rejects altered output paths,
byte counts, package order, or upstream graphs without reproducing layout-plan
validation.

Destination paths come only from `plan.packages[*].relative_path`. The caller
cannot supply, replace, reorder, or extend package destinations. A normalized
Unicode and case-fold collision preflight provides an additional fail-closed
guard before any filesystem work.

Validation order is:

1. materialization-plan result and canonical plan equality;
2. output-root value, absent destination, and canonical existing parent;
3. fresh source-file read and content verification;
4. source snapshot equality with the plan's verified file metadata;
5. source/output separation;
6. output-parent descriptor and identity recheck;
7. private bounded staging writes; and
8. atomic publication.

Plan and output-value failures therefore perform no source reads. Source
failures perform no output writes. Any later failure returns no successful
materialization and cleans private staging when it remains owned by the
operation.

## Exact verified-byte binding

The source bindings come unchanged from the materialization plan. At
materialization time the existing artifact-file pipeline:

- repeats its root, binding, file-type, alias, size, and aggregate checks;
- opens the root and every intermediate directory with descriptor-relative
  `O_DIRECTORY | O_NOFOLLOW` traversal where the platform supports it;
- opens each final source with `O_NOFOLLOW`;
- compares its descriptor identity and size to the inspected file;
- reads within the existing 64 MiB per-file and 256 MiB aggregate limits; and
- delegates the resulting immutable byte tuple once to
  `verify_class_world_artifact_contents`.

Descriptor-confined traversal is mandatory for this materialization contract;
unsupported platforms fail closed. This closes the previously noted
intermediate-directory check/open race for source reads used by this operation
without changing the existing public artifact-file verification result shape.

The exact byte objects passed to the existing verifier are retained only for
the duration of the call and are the byte objects written to staging. There is
no verify-then-reopen gap. A digest mismatch is a completed source verification
but a materialization failure, and no destination is created.

The fresh file-verification result must equal the plan's retained verification
result, including canonical bindings and byte counts. It is returned directly
in the materialization result so its existing diagnostics and digest match
state remain available without translation.

## Output confinement and alias safety

`output_root` must be an explicit absolute path naming a new directory. Its
parent must already exist, be a real directory, contain no symbolic-link path
component, and retain the same device/inode identity when opened for
descriptor-relative operations. Existing file, directory, and symbolic-link
destinations are never overwritten.

The output root must be outside the artifact source root. Planned output paths
are traversed relative to a newly created private staging-directory descriptor.
Every directory open uses `O_DIRECTORY | O_NOFOLLOW`; every file is created
with `O_EXCL | O_NOFOLLOW`. Unexpected path reuse, case or normalization alias,
symbolic link, or non-directory component therefore fails closed.

Diagnostics contain contract locations and package identities, not absolute
host paths.

## Bounded writes and atomicity

The only data written are the already-bounded verified byte tuple. Files are
written in canonical plan order in chunks of at most 1 MiB, with exact byte
counts retained in the result. Files use mode `0644`; output directories use
mode `0755`.

All package directories and files are built in a private mode-`0700` sibling
staging directory. Files and containing directories are synchronized before
the completed staging tree is atomically renamed to the absent output root.
No operation that can fail remains after a successful rename before returning
success.

If staging, writing, or atomic replacement fails, the output root is not a
successful materialization and descriptor-relative cleanup removes only the
operation-owned staging tree. Cleanup failure is reported explicitly and never
converted into success.

## Safety and trust boundary

A successful result proves that the bytes written at each planned destination
were the same bytes accepted by the existing content verifier during this
materialization call. It does not establish authenticity, approval,
publication status, archive safety, package semantics, or assembled release
integrity beyond those opaque package artifacts.

The materializer performs no archive parsing or extraction, package loading,
student-code execution, runtime registration, network, database, Git,
environment, clock, Pygame, authentication, signing, approval, external
publication, or deployment work.

Later contracts may define a deterministic assembled-output manifest and
digest, safe package-format parsing if required, attribution output, archive
construction, signing or attestation, approval, external publication, and
deployment.
