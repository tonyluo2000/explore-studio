# Deterministic Class-World Assembly Input Plan v0.1

> **Status:** Implemented pure in-memory composition of one successful package
> artifact inventory into a content-addressed assembly input plan. Artifact
> reading, artifact verification, materialization, execution, archive creation,
> signing, approval, publication, and deployment remain deferred.

Assembly Input Plan v0.1 answers one narrow question:

> What deterministic identity represents this exact verified release
> declaration and its canonically ordered package artifact identities?

```text
successful ClassWorldArtifactInventoryResult
        ↓
validate the upstream result boundary
        ↓
project declaration digest + ordered package artifact identities
        ↓
canonical UTF-8 JSON bytes + SHA-256
        ↓
immutable ClassWorldAssemblyPlan
```

## Scope and architecture position

This contract is the smallest assembly-planning primitive after package
artifact inventory. It preserves the successful inventory by object identity
and adds one deterministic digest over its assembly-relevant content
identities. It creates no output tree and resolves no artifact location.

The plan contains:

- contract version `"0.1"`;
- the exact successful `ClassWorldArtifactInventory`; and
- a SHA-256 `ClassWorldAssemblyInputDigest`.

The digest covers the verified release-declaration digest and, in canonical
release-pin order, each package ID, exact version, digest algorithm, and
artifact digest. Consequently, changing the declaration identity, package
order, package pin, or declared artifact content identity changes the plan
digest.

The plan digest identifies declared assembly inputs. It is not a digest of
artifact bytes, an assembled directory, or a release archive, and it does not
prove that any artifact matches its declaration.

## Public API

```python
from explore.packages import build_class_world_assembly_plan

result = build_class_world_assembly_plan(artifact_inventory_result)
if result.is_planned:
    assert result.plan is not None
    print(result.plan.input_digest.hex_digest)
```

The public contract includes:

- `build_class_world_assembly_plan`;
- `ClassWorldAssemblyPlan` and `ClassWorldAssemblyPlanResult`;
- `ClassWorldAssemblyInputDigest`;
- `ClassWorldAssemblyPlanIssue` and its stable issue-code enum;
- `SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION`; and
- `SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM`.

## Upstream gate and fail-closed behavior

The input must be the exact existing `ClassWorldArtifactInventoryResult` type
and must contain one inventory and no issues. Because the upstream frozen
dataclasses remain publicly constructible, the boundary also rejects a forged
or corrupted output graph when its contract version, runtime model types,
declaration digest representation, artifact tuple, package-pin agreement, or
artifact digest representation is incoherent.

This defensive output check does not call release-declaration verification,
recompute the release-declaration digest, rebuild the artifact inventory, read
artifact bytes, or independently sort or join package declarations. A failed
upstream result is returned as `INVENTORY_NOT_BUILT` rather than reinterpreted.

All failures are atomic: `plan` is `None` and the immutable result contains one
stable issue. No partial digest or plan escapes.

## Canonical digest bytes

The input digest is SHA-256 over compact UTF-8 JSON followed by one newline.
Object keys use this fixed order:

1. `contract_version`;
2. `release_declaration_digest`, containing `algorithm` then `hex_digest`; and
3. `package_artifacts`, whose entries contain `package_id`, `package_version`,
   `digest_algorithm`, then `digest_hex`.

Package array order comes directly from the successful upstream inventory.
JSON is emitted without insignificant whitespace and without ASCII-escaping
Unicode. No time, UUID, environment, filesystem path, or machine state enters
the digest.

## Safety boundary and deferred work

Planning performs no filesystem, network, database, Git, environment, clock,
randomness, subprocess, Pygame, runtime-target, or student-code operation. It
does not load packages, verify artifact bytes, copy assets, execute registration
plans, authenticate users, publish releases, or deploy anything.

Later contracts may add explicit artifact-file verification and resolution,
deterministic output layout and materialization, assembled-output hashing,
archive construction, attribution output, signing or attestation, approval,
publication, and deployment.
