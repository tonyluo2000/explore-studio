# Class-World Assembled-Output Manifest File Digest Verification v0.1

> **Status:** Implemented bounded readback and canonical SHA-256 verification
> for one explicit assembled-output manifest file. Artifact and output-tree
> rereads, signing, approval, publication, authentication, and deployment
> remain outside this contract.

This contract answers one narrow question:

> Does this explicitly supplied file represent the exact canonical manifest
> authorized by this successful verified materialization, and does that
> manifest match this explicitly supplied expected SHA-256 digest?

```text
explicit manifest path
        +
successful ClassWorldVerifiedMaterializationResult
        +
explicit ClassWorldAssembledOutputManifestDigest
        ↓
bounded strict UTF-8 read and strict JSON structure parsing
        ↓
bind parsed package fields and order to the existing manifest composer
        ↓
existing canonical serializer + existing SHA-256 manifest composition
        ↓
immutable digest comparison state
```

## Public API

```python
from explore.packages import (
    verify_class_world_assembled_output_manifest_file_digest,
)

result = verify_class_world_assembled_output_manifest_file_digest(
    "/explicit/path/assembled-output.json",
    materialization_result,
    expected_digest,
)
if result.is_verified:
    assert result.manifest is not None
    assert result.matches is True
```

The contract version is `"0.1"`. The maximum file size is 1 MiB.

## Inputs and validation order

The operation accepts only:

1. one explicit non-empty `str` or `pathlib.Path` manifest path;
2. one complete successful verified-materialization result; and
3. one explicit `sha256` expected digest containing exactly 64 lowercase
   hexadecimal characters.

Path and expected-digest validation precede materialization validation.
Materialization validation delegates to the existing assembled-output manifest
composer and therefore performs no filesystem access. The manifest path is not
inspected or opened if these authority inputs are invalid.

## Bounded file read

Only the supplied manifest path is inspected and opened. Its final component
must already exist, must be a regular file, and must not be a symbolic link.
The reader requests at most 1 MiB plus one detection byte and rejects oversized
content before UTF-8 decoding or JSON parsing.

The byte sequence must be strict UTF-8 without a byte-order mark. The reader
does not inspect the materialized output tree, source artifact paths, package
files, directories referenced by `relative_path`, or any other filesystem
location.

## JSON and manifest validation

The parser accepts one finite JSON object. It rejects malformed JSON,
non-finite numbers, excessive numeric or structural input, duplicate keys,
unknown fields, missing fields, wrong JSON types, unsupported contract values,
invalid digest encodings, and negative byte counts.

The top-level fields are exactly:

1. `contract_version`;
2. `packages`; and
3. `total_bytes`.

Every package has exactly:

1. `package_id`;
2. `package_version`;
3. `digest_algorithm`;
4. `digest_hex`;
5. `relative_path`; and
6. `bytes_written`.

JSON object key order and insignificant whitespace are not trusted as identity.
After structural parsing, the complete value must equal the canonical package
projection rebuilt by the existing assembled-output manifest composer. Package
array order is therefore significant and must remain the materialization
plan's canonical order. Missing, additional, reordered, or altered package
entries fail with no parsed manifest result.

## Canonical digest comparison

The actual digest is SHA-256 over the existing manifest serializer's canonical
UTF-8 JSON bytes, including its terminal line feed. It is not a digest of the
raw file bytes. A semantically identical input with different harmless
whitespace therefore produces the same actual manifest digest.

The existing manifest composer recomputes that canonical digest; this layer
does not reproduce hashing or serialization behavior. A well-formed unequal
expected digest returns `matches=False` with the actual and expected digests
preserved. It is not a verified result.

## Trust and excluded boundaries

Successful verification proves that the explicit file represents the exact
manifest projection of the supplied coherent verified materialization and
matches the supplied expected digest. The expected digest is comparison input,
not proof of authenticity, approval, or publication.

This tranche performs no artifact-content verification, materialization,
artifact or output-tree reread, archive parsing or extraction, package loading,
student-code execution, runtime registration, signing, approval,
authentication, publication, or deployment.

The previously recorded materialization documentation cleanup and filesystem
hardening notes remain separate follow-up work.
