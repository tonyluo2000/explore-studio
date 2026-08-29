# Deterministic Class-World Assembled-Output Manifest v0.1

> **Status:** Implemented pure in-memory manifest composition, canonical JSON
> serialization, and SHA-256 digesting over one successful verified
> materialization. Manifest file transport, readback, and digest verification
> remain deferred.

Assembled-Output Manifest v0.1 answers one narrow question:

> Given one complete verified materialization, what exact package artifacts
> were materialized at which plan-authorized paths, and what deterministic
> digest identifies that canonical manifest?

```text
successful ClassWorldVerifiedMaterializationResult
        ↓
validate the retained materialization against a canonically rebuilt plan
        ↓
project the exact materialized package tuple in plan order
        ↓
canonical compact JSON + terminal newline
        ↓
SHA-256 over the canonical UTF-8 bytes
        ↓
immutable ClassWorldAssembledOutputManifestResult
```

## Scope and architecture position

This is the smallest deterministic identity primitive after verified
materialization. It consumes only the successful immutable materialization
result already produced by that boundary. It does not accept caller-selected
packages, paths, digests, byte counts, or ordering.

The manifest records only the exact package/artifact set authorized by the
retained materialization plan and reported as successfully written. Explorer
Packages remain independent entries identified by package ID and version.

The composer performs no filesystem access. In particular, it does not reopen
the published output, reread source artifacts, or hash artifact bytes. Source
bytes and declared artifact digests have already been bound and verified by
the upstream materialization chain.

## Public API

```python
from explore.packages import (
    build_class_world_assembled_output_manifest,
    serialize_class_world_assembled_output_manifest,
)

result = build_class_world_assembled_output_manifest(materialization_result)
if result.is_built:
    assert result.manifest is not None
    assert result.digest is not None
    canonical_text = serialize_class_world_assembled_output_manifest(result.manifest)
```

The public contract includes:

- `build_class_world_assembled_output_manifest`;
- `serialize_class_world_assembled_output_manifest`;
- `ClassWorldAssembledOutputPackage`;
- `ClassWorldAssembledOutputManifest` and its digest and result models;
- `ClassWorldAssembledOutputManifestIssue` and its stable issue-code enum;
- `SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION`; and
- `SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM`.

The contract version is `"0.1"`; the digest algorithm is `"sha256"`.

## Canonical manifest fields and order

The immutable in-memory manifest retains these fields in order:

1. `contract_version`;
2. `materialization` — the exact successful upstream materialization object;
3. `packages` — the canonical package projection; and
4. `total_bytes`.

The retained `materialization` object carries the trust chain but is not
embedded in the canonical JSON. The serialized top-level object has exactly
these fields in order:

1. `contract_version`;
2. `packages`; and
3. `total_bytes`.

Every `packages` entry has exactly these fields in order:

1. `package_id`;
2. `package_version`;
3. `digest_algorithm`;
4. `digest_hex`;
5. `relative_path`; and
6. `bytes_written`.

Package entries remain in the materialization plan's canonical order. Each
identity and declared artifact digest comes from the plan-authorized artifact;
each relative path comes from the corresponding plan entry; and each byte
count comes from the corresponding successful materialized package.

## Canonical JSON serialization and digest

Serialization uses JSON with:

- the exact field and package order above;
- UTF-8 text with non-ASCII characters preserved rather than ASCII-escaped;
- compact separators: `,` between values and `:` between keys and values;
- no indentation or insignificant spaces; and
- exactly one terminal line-feed byte (`0x0a`).

The manifest digest is lowercase hexadecimal SHA-256 over the complete
canonical UTF-8 byte sequence, including the terminal line feed:

```text
hex_digest = sha256(canonical_json_text.encode("utf-8")).hexdigest()
```

Equivalent successful materializations therefore produce identical canonical
text and digest values.

## Fail-closed upstream validation

The input must be the exact verified-materialization result type with no
issues, one complete materialization, and the same retained source-verification
object exposed by the result envelope.

Before projection, the composer:

- requires the supported verified-materialization contract and exact upstream
  model types;
- rebuilds the existing pure materialization plan from its retained file
  verification and requires equality with the supplied plan;
- requires the fresh source verification to equal the plan's retained
  verification;
- requires materialized and planned package tuples to have identical
  cardinality and canonical order;
- requires every materialized package to retain its exact planned package;
- requires every written byte count to equal the verified source byte count;
  and
- requires package, materialization, and plan totals to agree.

Missing, malformed, incomplete, forged, reordered, truncated, extended, or
non-matching state returns no manifest and no digest. Serialization separately
rejects a manifest that no longer matches its retained materialization.

These checks call the existing pure plan builder; they do not reproduce source
file verification, artifact hashing, or materialization behavior.

## Trust and deferred boundaries

This contract inherits, but does not expand, the verified-materialization
trust boundary. A successful result records the identities, declared digests,
authorized paths, and byte counts represented by a coherent successful
materialization. It does not independently prove filesystem contents,
authenticity, approval, publication status, archive safety, or package
semantics.

The composer performs no filesystem reads or writes, archive parsing or
extraction, package loading, student-code execution, runtime registration,
network access, authentication, signing, approval, external publication, or
deployment.

Persisting this canonical JSON, reading it back, and verifying a supplied or
pinned manifest digest are not part of v0.1. A later bounded transport and
readback/digest-verification contract may add those capabilities without
changing this in-memory composition boundary.
