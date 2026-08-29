# Deterministic Class-World Materialization Layout Plan v0.1

> **Status:** Implemented pure in-memory output-layout planning from one
> complete matching package artifact-file verification result. Filesystem
> materialization, artifact rereads, extraction, assembled-output hashing,
> execution, signing, approval, publication, and deployment remain deferred.

Materialization Layout Plan v0.1 answers one narrow question:

> Given a complete bounded artifact-file verification whose package contents
> all match their declarations, what canonical package-separated output paths
> and byte-count expectations would a later materializer use?

```text
complete ClassWorldArtifactFileVerificationResult
        ↓
validate only the retained upstream output needed by this layer
        ↓
require every delegated package digest comparison to match
        ↓
project canonical package-separated relative output paths
        ↓
immutable ClassWorldMaterializationPlan
```

## Scope and architecture position

This is the smallest deterministic output-layout primitive after bounded
artifact-file verification. It performs no filesystem access and produces no
directory, artifact, archive, or runtime state.

The plan retains the exact successful file-verification result and contains,
in existing canonical assembly-plan order:

- the exact package artifact declaration;
- the exact successful package artifact file-read metadata;
- one generated output-relative path; and
- the aggregate verified byte count.

Every package has an independent layout boundary:

```text
packages/{package_id}/{package_version}/artifact
```

The final `artifact` name intentionally has no inferred archive or media
extension because verified package artifact bytes remain opaque at this layer.

## Public API

```python
from explore.packages import build_class_world_materialization_plan

result = build_class_world_materialization_plan(file_verification_result)
if result.is_planned:
    assert result.plan is not None
    print(result.plan.packages[0].relative_path)
```

The public contract includes:

- `build_class_world_materialization_plan`;
- `ClassWorldPackageMaterialization`;
- `ClassWorldMaterializationPlan` and its result model;
- `ClassWorldMaterializationPlanIssue` and its stable issue-code enum; and
- `SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION`.

The contract version is `"0.1"`.

## Upstream gate and mismatch behavior

The upstream input must be the exact existing artifact-file verification
result type with its supported contract version, no file issues, non-empty
canonical file-read metadata, and one completed content-verification result.

Because upstream frozen dataclasses are publicly constructible, this boundary
checks only invariants required to derive and retain safe layout output:

- file reads, content-verification packages, and planned artifacts have equal
  cardinality and canonical order;
- each retained object has its exact public model type;
- package identity and version agree across the plan, content result, and file
  binding;
- declared and recomputed digest representations are coherent with `matches`;
- file and aggregate byte counts remain within the existing verified limits;
  and
- package identities are valid and unique for separated output paths.

These are defensive output-graph checks. This layer does not call or reproduce
declaration verification, inventory construction, assembly-input digesting,
content hashing, path binding, file inspection, or bounded reads.

A valid content mismatch is a completed upstream verification state, but it is
not eligible for layout planning. Every mismatching package produces one
deterministic `ARTIFACT_CONTENT_MISMATCH` issue in canonical package order, and
the result contains no partial plan.

## Determinism and atomicity

No caller-selected destination paths enter the v0.1 contract. Successful
package order comes unchanged from the verified assembly plan, and each output
path is a fixed projection of its exact package ID and version. Equivalent
verified results therefore produce equal frozen plans.

Every failure is atomic: `plan` is `None`, diagnostics are immutable and
stable, and no partial layout escapes.

## Trust, filesystem, and TOCTOU boundary

A successful plan proves only layout eligibility for the retained verification
state. It does not prove authenticity, approval, publication, archive safety,
or assembled-output integrity. It is not authority to reopen or copy a source
file later: a future materializer must define how bytes remain bound to the
verification that admitted them.

The documented intermediate-directory TOCTOU limitation remains future
hardening in the existing artifact-file verification layer. This planning
contract neither depends on nor changes that limitation because it performs no
path traversal or file access.

Planning performs no writes, reads, extraction, package loading, student-code
execution, runtime registration, network, database, Git, environment, clock,
randomness, subprocess, Pygame, authentication, signing, approval, publication,
or deployment work.

The downstream
[Verified Class-World Package Artifact Materialization v0.1](class-world-verified-materialization-v0.1.md)
now reverifies descriptor-confined source files and atomically places the exact
verified byte tuple at only these plan-authorized paths. Later contracts may
define deterministic assembled-output manifests and hashing, safe archive
parsing, attribution output, archive construction, signing or attestation,
approval, external publication, and deployment.
