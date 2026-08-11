# Class-World Release Declaration Digest Verification v0.1

> **Status:** Implemented pure in-memory validation and equality comparison
> between a supplied expected declaration digest and the digest recomputed from
> a release declaration. Verified declaration-file readback is implemented as
> a separate composition layer. Raw file-byte hashing, artifact inventories,
> signing, trust-source policy, publication, and deployment remain deferred.

Class-World Release Declaration Digest Verification v0.1 answers one narrow
question:

> Does this expected declaration digest equal the digest of this declaration's
> current canonical serialized bytes?

```text
immutable expected ClassWorldReleaseDeclarationDigest
        +
immutable ClassWorldReleaseDeclaration
        ↓
validate expected digest
        ↓
existing declaration digest computation
        ↓
new immutable actual digest
        ↓
complete expected-versus-actual model equality
        ↓
immutable ClassWorldReleaseDeclarationDigestVerificationResult
```

Digest verification confirms that an expected declaration digest equals the
digest recomputed from the declaration's current canonical serialization. A
matching digest does not prove who created the declaration, whether its
provenance claims are true, or whether package and artifact files match those
claims.

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
7. [Release-declaration digest computation](class-world-release-declaration-digest-v0.1.md)
   identifies canonical serialized declaration bytes.
8. Release-declaration digest verification validates an expected digest,
   recomputes step 7, and compares the complete immutable digest models.
9. [Release-declaration file digest verification](class-world-release-declaration-file-digest-verification-v0.1.md)
   composes the authoritative file reader with this verifier after a successful
   read.
10. Future layers may verify raw stored bytes, inventory and assemble artifacts,
   sign or attest content, define trust sources, approve, publish, and deploy.

This contract implements only step 8. It does not read a file, verify package
or artifact bytes, validate provenance truth, or establish authenticity.

## Verification contract version

The verification contract version is:

```python
SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_VERIFICATION_CONTRACT_VERSION = "0.1"
```

It is distinct from:

- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION`, which versions the
  release declaration model and JSON schema;
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION`,
  which versions release-declaration filesystem transport;
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION`, which
  versions canonical digest computation; and
- this verification contract, which versions expected-input validation and
  digest-comparison semantics.

All four values are currently `"0.1"`, but they are independent contracts.

## Public API

```python
from explore.packages import (
    compute_class_world_release_declaration_digest,
    verify_class_world_release_declaration_digest,
)

expected_digest = compute_class_world_release_declaration_digest(declaration)
result = verify_class_world_release_declaration_digest(
    declaration,
    expected_digest,
)

assert result.matches is True
assert result.expected_digest is expected_digest
assert result.actual_digest == expected_digest
```

The intentional public surface is:

- `verify_class_world_release_declaration_digest`;
- `ClassWorldReleaseDeclarationDigestVerificationResult`; and
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_VERIFICATION_CONTRACT_VERSION`.

No bare-string overload, actual-digest argument, or custom mismatch exception
is provided. File readback uses the separate composition API rather than
overloading this in-memory verifier.

## Expected digest input

The expected input must be a
`ClassWorldReleaseDeclarationDigest`. A `str`, mapping, object, or other value
is not coerced and raises `TypeError`.

The supplied model is external verification input and is validated before the
declaration digest is recomputed. It must contain:

- `algorithm` exactly equal to `"sha256"`; and
- `hex_digest` with runtime type `str`, exactly 64 characters, using only
  lowercase `0` through `9` and `a` through `f`.

Malformed models raise `ValueError`. Verification does not lowercase, strip,
truncate, normalize, repair, or reinterpret input. Examples rejected by v0.1
include:

```text
SHA256
sha-256
sha512
uppercase hexadecimal
63 or 65 characters
non-hexadecimal characters
leading or trailing whitespace
empty text
non-string algorithm or hexadecimal value
```

## Validation ordering

The deterministic operation order is:

1. require the exact expected digest model type;
2. validate its algorithm;
3. validate its lowercase hexadecimal representation;
4. recompute the actual digest from the declaration;
5. compare the complete expected and actual digest models; and
6. construct the immutable result.

Malformed expected input therefore fails before declaration serialization or
digest computation. A valid expected digest causes exactly one actual digest
computation.

## Actual digest recomputation

Verification always calls:

```python
compute_class_world_release_declaration_digest(
    declaration
)
```

The existing digest API remains the sole digest authority. This verification
layer does not call the serializer, import `hashlib`, construct JSON, encode
UTF-8, reproduce final-newline rules, select an algorithm, or accept a cached
actual digest.

The digest is recomputed on every call from the declaration's current
canonical serialization. It is never read from file metadata, package
metadata, a cache, database, registry, or global variable.

## Matching semantics

For valid expected and actual digest models:

```python
matches = expected_digest == actual_digest
```

Complete dataclass equality means both `algorithm` and `hex_digest`
participate. Verification does not compare the hexadecimal text while ignoring
algorithm identity.

A match returns normally with:

```python
result.matches is True
```

A matching digest confirms byte-level equality with the expected digest under
the v0.1 declaration digest contract. It makes no additional security or
artifact claim.

## Mismatch semantics

A valid expected digest that differs from the recomputed actual digest returns:

```python
ClassWorldReleaseDeclarationDigestVerificationResult(
    expected_digest=expected_digest,
    actual_digest=actual_digest,
    matches=False,
)
```

A digest mismatch is a normal verification result, not an exception. v0.1
defines no `DigestMismatchError`, `IntegrityError`, or `VerificationError`.
Both digests remain visible to the caller.

## Immutable result

`ClassWorldReleaseDeclarationDigestVerificationResult` is a frozen dataclass
containing only:

- `expected_digest`, the exact supplied immutable object;
- `actual_digest`, the newly recomputed immutable digest; and
- `matches`, the deterministic Boolean result of complete model equality.

It contains no timestamp, path, filename, Git identity, host or user identity,
signer, certificate, trust level, approval, publication status, explanation
text, or mutable diagnostics.

## Error behavior

The error boundary distinguishes malformed verification input from a valid
mismatch:

- wrong expected object type raises `TypeError`;
- malformed expected algorithm or hexadecimal value raises `ValueError`;
- wrong declaration input preserves the existing digest/serializer
  `TypeError`;
- an inconsistent declaration preserves the existing serializer `ValueError`;
  and
- a valid unequal digest returns `matches=False`.

No result is returned after an exception. Neither input is mutated, repaired,
normalized, or partially evaluated.

## Determinism

Repeated verification with equivalent declarations and equal expected digests
returns equal verification results. No clock, UUID, randomness source,
environment variable, working directory, filesystem metadata, Git state,
network service, database, registry, cache, or mutable global state
participates.

Digest values are not secrets in this contract. Normal immutable value
equality is sufficient; no HMAC or constant-time secret comparison is used.

## Relationship to file transport

[Release-declaration file transport](class-world-release-declaration-file-transport-v0.1.md)
moves canonical JSON through explicit local paths. This verification API does
not invoke that transport and does not read, reopen, stat, hash, or compare a
release-declaration file.

[Class-World Release Declaration File Digest Verification v0.1](class-world-release-declaration-file-digest-verification-v0.1.md)
is the separate implemented reader-first composition contract. It preserves
reader failures before invoking this verifier and verifies the canonical
declaration represented by a file, not the file's raw bytes.

## No provenance truth verification

The release declaration contains engine, Student API, cohort, and package
provenance values. A match confirms only that those declared values participate
in the canonical bytes represented by the expected digest.

It does not independently prove which engine or Student API ran, which packages
executed, the identity of a cohort, the truth of package provenance, or any Git
history.

## No authenticity guarantee

An expected digest has no trust-source semantics in v0.1. A match does not
identify who supplied it or who created the declaration. This contract uses no
HMAC, signer, key, certificate, trust store, approval authority, or
attestation.

The result must not be interpreted as signature verification, release
authenticity verification, or trusted-release verification. Signing,
attestation, and trust-source policy remain future layers.

## No artifact verification

Verification covers no:

- Explorer Package source or archive bytes;
- package assets;
- class-world manifest files;
- generated files or output directories;
- assembled class-world content;
- ZIP or TAR archives; or
- deployment bundles.

It creates no package, asset, artifact, or archive inventory and performs no
assembly or copying. A matching declaration digest says nothing about whether
these files match the declaration.

## Safety and purity boundary

Release-declaration digest verification performs no:

- filesystem reads, writes, metadata inspection, walking, or temporary files;
- release-declaration file transport or verified readback;
- package validation, loading, planning, or application;
- artifact, asset, package, or output inventory;
- class-world assembly, copying, archive creation, or runtime mutation;
- Pygame, engine lifecycle, scene, renderer, or event-loop work;
- HMAC, signing, signature verification, certificate, or key management;
- network, HTTP, database, registry, cloud-storage, or Git access;
- environment, clock, randomness, UUID, cache, or mutable global access;
- authentication, authorization, approval, publication, or deployment; or
- persistent telemetry, audit-record, or recovery-record creation.

Its operational dependencies are limited to the existing declaration model,
digest model, public digest compute API, and immutable verification result
model.

## Deferred work

Deferred work includes:

- raw release-file byte digests, if separately required;
- artifact, package, asset, and output inventories;
- package and asset hashes;
- class-world assembly and asset materialization;
- release artifact and archive creation;
- archive hashing;
- signing, key management, attestations, and trust-source policy;
- approval and publication;
- authentication, authorization, registries, and online storage;
- deployment; and
- persistent audit and recovery records.
