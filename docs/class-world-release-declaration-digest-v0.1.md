# Deterministic Class-World Release Declaration Digest v0.1

> **Status:** Implemented pure in-memory SHA-256 digest computation for the
> canonical serialized class-world release declaration. Pure in-memory digest
> verification and verified declaration-file readback are implemented
> separately. Raw file-byte hashing, artifact inventories, class-world
> assembly, signing, publication, and deployment remain deferred.

Deterministic Class-World Release Declaration Digest v0.1 identifies the exact
canonical release-declaration text produced by the existing serializer:

```text
immutable ClassWorldReleaseDeclaration
        ↓
existing canonical serializer
        ↓
canonical UTF-8 declaration bytes
        ↓
SHA-256
        ↓
immutable ClassWorldReleaseDeclarationDigest
```

The digest identifies the canonical serialized release declaration. It does
not identify an assembled class-world artifact, package archive, asset set,
runtime output, publication state, or deployment.

## Architecture position

The implemented layers remain distinct:

1. `ClassWorldConfiguration` declares authoritative immutable class-world
   composition.
2. Class-world manifest JSON deterministically serializes configuration.
3. Manifest file transport moves manifest JSON at explicit local paths.
4. `ClassWorldReleaseDeclaration` records release identity and declared
   provenance.
5. Release-declaration JSON deterministically serializes and strictly parses
   that declaration.
6. Release-declaration file transport moves that JSON at explicit bounded
   local paths.
7. Release-declaration digest computation identifies the canonical serialized
   declaration bytes.
8. [Release-declaration digest verification](class-world-release-declaration-digest-verification-v0.1.md)
   validates a supplied expected digest, recomputes step 7, and compares the
   complete immutable digest models.
9. [Release-declaration file digest verification](class-world-release-declaration-file-digest-verification-v0.1.md)
   reads a declaration file through the authoritative transport and invokes
   step 8 on the resulting declaration; it does not hash raw file bytes.
10. Future layers may verify stored bytes, inventory and assemble artifacts,
   sign or attest content, approve, publish, and deploy releases.

This contract implements only step 7. It does not move files, compare a stored
file, or make claims about step 9.

## Contract constants

The digest contract version is:

```python
SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION = "0.1"
```

The only v0.1 algorithm identifier is:

```python
SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM = "sha256"
```

The digest contract version is distinct from:

- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION`, which versions the
  in-memory model and JSON schema;
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION`,
  which versions explicit filesystem transport behavior; and
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_VERIFICATION_CONTRACT_VERSION`,
  which versions expected-digest validation and equality semantics; and
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION`,
  which versions reader-first file-readback composition semantics.

All five are currently `"0.1"`, but they describe independent contracts.

## Public API

```python
from explore.packages import compute_class_world_release_declaration_digest

digest = compute_class_world_release_declaration_digest(declaration)

assert digest.algorithm == "sha256"
assert len(digest.hex_digest) == 64
```

The intentional public surface is:

- `compute_class_world_release_declaration_digest`;
- `ClassWorldReleaseDeclarationDigest`;
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION`; and
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM`.

`ClassWorldReleaseDeclarationDigest` is a frozen dataclass containing only:

- `algorithm`, exactly `"sha256"` for successful v0.1 computation; and
- `hex_digest`, exactly 64 lowercase hexadecimal characters.

It contains no time, path, filename, Git identity, host identity, salt, nonce,
signature, byte length, or verification status.

## Exact digest input

The SHA-256 input is exactly:

```python
serialize_class_world_release_declaration(
    declaration
).encode("utf-8")
```

Every byte is significant. The input therefore preserves the serializer's:

- schema-defined key order;
- two-space indentation;
- literal Unicode output;
- exact ordered package array;
- newline policy; and
- exactly one final newline.

The final newline is part of the digest input. The digest implementation does
not strip, normalize, re-indent, parse, rebuild, or apply platform newline
conversion to the serializer output.

## Canonical serializer dependency

`serialize_class_world_release_declaration` is the sole byte authority. Digest
computation does not independently construct JSON or duplicate schema,
configuration, package-order, Unicode, or newline behavior.

If a future serializer contract intentionally changes, the digest contract
must be versioned explicitly. v0.1 does not attempt algorithm or serialization
negotiation.

## UTF-8 and Unicode behavior

Canonical text is encoded with UTF-8. The serializer uses literal Unicode
output rather than an independently generated escaped-ASCII representation.
Digest computation introduces no NFC, NFD, locale, or other Unicode
normalization. Canonical texts with different UTF-8 byte sequences have
different SHA-256 inputs.

## Determinism and sensitivity

Equivalent valid declarations serialize to equal canonical text and therefore
produce equal digest models. Repeated computation over one declaration is
equal. No clock, UUID, randomness source, environment variable, working
directory, filesystem metadata, Git state, network service, database, or
mutable registry participates.

The digest changes when canonical serialized declaration fields change,
including release identity, class-world identity or version, engine version,
cohort identity, or ordered package pins. Package count and order are part of
the canonical bytes. Upstream builders still decide which values are valid;
digest computation never bypasses those invariants merely to produce a hash.

## Error behavior

Digest computation preserves serializer failures:

- a wrong programmer-level input propagates `TypeError`; and
- a manually inconsistent declaration propagates `ValueError`.

No digest is returned after either failure. The implementation does not repair,
coerce, normalize, reconstruct, or partially hash an invalid declaration.

## Relationship to file transport

Release-declaration file transport writes the same canonical UTF-8 expression
used as the digest input. A successfully written canonical declaration file
therefore contains bytes equal to the in-memory digest input.

Digest computation itself performs no file I/O. It does not read the written
file, reopen a destination, hash a caller-supplied path, or verify readback.
There is no v0.1 file-digest or file-verification API.

## Relationship to digest verification

The separate
[Class-World Release Declaration Digest Verification v0.1](class-world-release-declaration-digest-verification-v0.1.md)
validates a supplied expected digest, calls this public digest computation API
exactly once, and compares the complete immutable digest models. It does not
serialize or hash independently.

A matching digest confirms equality with the expected digest under this
canonical byte contract. It does not establish authenticity, provenance truth,
package integrity, artifact integrity, approval, or publication status. A
valid mismatch is a normal verification result.

## Declaration digest versus artifact digest

This digest covers release-declaration metadata only. It does not cover:

- Explorer Package source or archive bytes;
- package assets;
- class-world manifest files;
- generated class-world files;
- output directories;
- archive membership;
- executables; or
- deployment content.

The digest therefore cannot establish that package files or assembled output
match the declaration. Artifact inventories and artifact digests require a
separate future contract.

## Digest versus signature

SHA-256 provides deterministic byte identity, not authenticity. This contract
uses no HMAC, key, certificate, signature, signer identity, approval record, or
attestation. Anyone with the canonical declaration bytes can compute the same
digest.

The digest does not mean that a declaration is authentic, approved, published,
or produced by a trusted party. Signing and trust policy remain separate future
layers.

## Safety and purity boundary

Release-declaration digest computation performs no:

- filesystem reads, writes, metadata inspection, walking, or temporary files;
- release-declaration file transport or verified readback;
- package validation, loading, planning, or application;
- artifact, asset, package, or output inventory;
- class-world assembly, copying, archive creation, or runtime mutation;
- Pygame, engine lifecycle, scene, renderer, or event-loop work;
- HMAC, salting, key derivation, signing, signature verification, or key
  management;
- network, HTTP, database, registry, cloud-storage, or Git access;
- authentication, authorization, approval, publication, or deployment; or
- persistent audit-record creation.

The implementation uses only the existing canonical serializer and Python's
standard-library `hashlib.sha256` over in-memory bytes.

## Deferred work

Deferred work includes:

- verified release-declaration file readback;
- declaration-file digest verification;
- artifact, package, asset, and output inventories;
- package and asset digests;
- class-world assembly and asset materialization;
- release artifact and archive creation;
- archive hashing;
- signing, key management, attestations, and trust policy;
- approval and publication;
- authentication, authorization, registries, and online storage;
- deployment; and
- persistent audit and recovery records.
