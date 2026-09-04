# Deterministic Class-World Release Bundle v0.1

> **Status:** Implemented deterministic, self-contained ZIP creation and bounded
> readback verification from one already verified materialized Class-World
> output tree. Signing, approval, authentication, registries, publication,
> deployment, and student-code execution remain outside this contract.

This contract answers two narrow questions:

> What single portable artifact contains the canonical release declaration,
> canonical assembled-output manifest, and every verified package payload?

> Does an explicit archive still have the exact canonical structure, contents,
> metadata, and whole-bundle SHA-256 expected from that verified pipeline?

```text
successful ClassWorldOutputTreeVerificationResult
        +
explicit verified output root
        +
explicit absent destination
        ↓
rebuild and validate retained canonical release metadata
        ↓
descriptor-confined reread and SHA-256 verification of package payloads
        ↓
canonical stored ZIP written to an operation-owned sibling staging file
        ↓
atomic absent-destination publication
        ↓
SHA-256 over the complete archive bytes
```

## Public API

```python
from explore.packages import (
    verify_class_world_release_bundle_file,
    write_class_world_release_bundle,
)

written = write_class_world_release_bundle(
    output_tree_result,
    "/absolute/materialized-output",
    "/absolute/releases/class-world.zip",
)
if written.is_written:
    verified = verify_class_world_release_bundle_file(
        "/absolute/releases/class-world.zip",
        output_tree_result,
        written.digest,
    )
    assert verified.is_verified
```

The contract version is `"0.1"`. Whole-bundle and member content identities
use lowercase hexadecimal SHA-256. The public surface also includes immutable
bundle, entry, digest, issue, write-result, and verification-result models.

## Canonical member set and ordering

The archive is a ZIP file with no archive comment and exactly these regular-file
members in this order:

1. `metadata/class-world.release.json` — the existing canonical release
   declaration serialization;
2. `metadata/assembled-output.manifest.json` — the existing canonical
   assembled-output manifest serialization; and
3. every verified package payload at its manifest-authorized relative path, in
   canonical assembled-output manifest package order.

No directory entries, additional files, duplicate members, aliases, generated
indexes, signatures, or mutable host metadata are present. Package member paths
remain the existing canonical
`packages/{package_id}/{package_version}/artifact` paths.

The release declaration binds release and class-world identity, engine and
Student API versions, cohort identity, and exact ordered package pins. The
assembled-output manifest binds those packages to canonical output paths,
content digests, byte counts, and the aggregate package byte total. Together
with the payloads, these make the ZIP a self-contained Phase C release artifact.

## Deterministic ZIP profile

Every member uses the same fixed metadata:

- storage method: ZIP `STORED` (no compression);
- timestamp: `1980-01-01 00:00:00`, the ZIP epoch;
- creator system: Unix (`3`);
- file type and permissions: regular file, mode `0644`;
- internal attributes: zero;
- per-member extra field and comment: empty; and
- archive comment: empty.

The writer supplies all member bytes before each entry is written, uses no
clock, environment, hostname, user/group identity, randomness, source mtime,
filesystem traversal order, or compression library output in archive content.
Equivalent verified inputs therefore produce byte-identical archives even when
their source and output roots differ.

The bundle digest is SHA-256 over every raw archive byte:

```text
hex_digest = sha256(archive_bytes).hexdigest()
```

This digest is distinct from the canonical release-declaration digest, assembly
input digest, package digests, and assembled-output manifest digest.

## Input validation and payload reread

Creation consumes only an exact successful
`ClassWorldOutputTreeVerificationResult`. It rebuilds the existing
assembled-output manifest from the retained materialization graph, requires
equality with the supplied manifest and verified artifact projection, and
recomputes the retained release-declaration digest.

The output root and destination must be explicit absolute paths. The output
root is reopened with the existing mandatory descriptor-confinement facilities.
Every manifest-authorized payload is reread without following symbolic links,
bounded by the existing 64 MiB per-package and 256 MiB aggregate limits, and
must still match its manifest byte count and SHA-256. The operation never
enumerates or includes unrelated output-tree files.

The destination parent must exist, be a real directory, and contain no symbolic
link component. The destination must be absent. The archive is completed and
synchronized in an operation-owned sibling staging file, assigned mode `0644`,
and published without replacing an existing path. Failure never reports a
successful bundle.

## Readback verification

Readback accepts one explicit absolute regular archive path, the authoritative
verified output-tree result, and one expected whole-bundle digest. It reads at
most 260 MiB and never extracts archive members.

It requires:

- a valid ZIP with the exact canonical ordered member names and no archive
  comment;
- the fixed metadata profile on every member;
- exact canonical release-declaration and assembled-output manifest bytes;
- exact manifest byte counts and SHA-256 for every package payload; and
- equality between the recomputed raw archive SHA-256 and the explicit expected
  bundle digest.

A structurally and semantically valid archive with a different expected digest
retains immutable `matches=False` comparison state but is not verified. Any
structural, metadata, content, bounds, or upstream-coherence failure returns no
verified bundle.

## Trust boundary

Successful creation and readback prove deterministic composition and integrity
relative to the already verified local pipeline and the supplied expected
SHA-256. SHA-256 is identity, not authenticity. This contract does not establish
who produced or approved a release, whether provenance statements are true, or
whether package contents are safe to execute.

The bundle contract performs no archive extraction, package loading,
student-code execution, runtime registration, signing, attestation, approval,
authentication, registry access, network access, publication, deployment, or
unrelated platform hardening.
