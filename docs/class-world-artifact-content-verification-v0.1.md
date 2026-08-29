# Class-World Package Artifact Content Verification v0.1

> **Status:** Implemented pure in-memory SHA-256 verification of one immutable
> artifact byte payload per package in a successful assembly-input plan.
> Artifact-file reading and resolution, materialization, execution, archive
> creation, signing, approval, publication, and deployment remain deferred.

Artifact Content Verification v0.1 answers one narrow question:

> Do these caller-supplied package artifact bytes match every declared artifact
> digest in this successfully built assembly-input plan?

```text
successful ClassWorldAssemblyPlanResult
        +
immutable tuple of artifact bytes in canonical plan order
        ↓
validate upstream result boundary and payload cardinality/types
        ↓
recompute SHA-256 for each payload
        ↓
immutable ordered match state
```

## Scope and architecture position

This is the smallest integrity primitive after deterministic assembly-input
planning. It preserves the exact successful `ClassWorldAssemblyPlan` by object
identity and recomputes only package artifact content digests.

It does not rebuild the inventory, recompute the assembly-input digest, resolve
package identities, or independently sort package declarations. The plan's
existing artifact tuple remains the canonical source of package order and
expected content identity.

The caller supplies one immutable `bytes` value per planned package artifact.
This contract intentionally accepts no paths. A later file composition layer
may define explicit bounded reads and then delegate the resulting bytes to this
pure verifier.

## Public API

```python
from explore.packages import verify_class_world_artifact_contents

result = verify_class_world_artifact_contents(
    assembly_plan_result,
    (first_artifact_bytes, second_artifact_bytes),
)

if result.is_complete:
    assert result.verification is not None
    print(result.verification.all_match)
```

The public contract includes:

- `verify_class_world_artifact_contents`;
- `ClassWorldArtifactContentVerification` and its result model;
- `ClassWorldPackageArtifactContentVerification`;
- `ClassWorldPackageArtifactContentDigest`;
- `ClassWorldArtifactContentVerificationIssue` and its stable issue-code enum;
  and
- `SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION`.

The only supported contract version and digest algorithm are `"0.1"` and
`"sha256"`, respectively. The digest algorithm remains sourced from the
existing package artifact declaration contract.

## Upstream gate

The upstream input must be the exact existing `ClassWorldAssemblyPlanResult`
type and must contain one plan and no issues. A missing, wrong-type, failed, or
malformed result fails before artifact contents are inspected.

Because the frozen upstream dataclasses are publicly constructible, the gate
checks only fields required by this layer: the assembly-plan contract version,
input-digest model and representation, inventory model, non-empty artifact
tuple, exact artifact declaration types, and supported artifact digest
representations. It does not call the assembly-plan builder, inventory builder,
release-declaration verifier, or any canonical assembly-input serializer.

## Content contract and deterministic diagnostics

`artifact_contents` must be an exact tuple whose length equals the plan's
artifact count. Each entry must be exact immutable `bytes`; mutable
`bytearray`, `memoryview`, strings, paths, streams, and arbitrary objects are
rejected without hashing.

Container and count failures return one stable issue. When count is correct,
every invalid entry is reported in ascending index order. Any issue makes the
operation atomic: `verification` is `None`, and no partial package digest state
escapes.

For a valid payload tuple, every package is hashed exactly once in canonical
plan order. Equivalent plans and bytes produce equal frozen results. Output
retains each exact artifact declaration, a freshly recomputed SHA-256 digest,
and a Boolean `matches` value.

Digest mismatch is normal completed verification state, not a structural
issue. `result.is_complete` remains true, the package's `matches` is false, and
aggregate `all_match` is false. No input is repaired, reordered, or replaced.

## Integrity and trust boundary

A matching result proves only that the supplied bytes hash to the content
identities declared in the supplied plan. It does not prove:

- where the bytes came from or whether they came from files;
- that the expected digests are trusted, approved, authentic, or published;
- archive membership, format, path safety, package validity, or provenance;
- assembled-output integrity; or
- signer, user, or deployment identity.

## Safety boundary and deferred work

Verification performs no filesystem, path, network, database, Git,
environment, clock, randomness, subprocess, Pygame, runtime-target, or
student-code operation. It does not parse archives, load Explorer Packages,
copy assets, execute registration plans, authenticate users, sign or approve
content, publish releases, or deploy anything.

Later contracts may add explicit artifact-file binding and bounded read-only
transport, deterministic output layout and materialization, assembled-output
hashing, archive construction, attribution output, signing or attestation,
approval, publication, and deployment.
