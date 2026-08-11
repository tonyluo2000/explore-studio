# Class-World Release Declaration File Digest Verification v0.1

> **Status:** Implemented read-only composition of the existing release-
> declaration file reader and in-memory declaration digest verifier. Raw file-
> byte hashing, artifact verification, authenticity, trust, approval,
> publication, and deployment remain deferred.

Class-World Release Declaration File Digest Verification v0.1 answers one
narrow question:

> Can this explicit release-declaration file be read under the existing
> transport and declaration contracts, and if so, does the declaration it
> represents canonicalize to the supplied expected declaration digest?

```text
explicit str or pathlib.Path
        +
authoritative ClassWorldConfiguration
        +
expected ClassWorldReleaseDeclarationDigest
        ↓
existing release-declaration file reader
        ↓
parsed and built ClassWorldReleaseDeclaration
        ↓
existing in-memory declaration digest verifier
        ↓
immutable file digest verification result
```

This operation does not hash raw file bytes. It reads, parses, and builds a
declaration, then the existing digest API canonically reserializes that
declaration before hashing and comparison.

## Architecture position

The implemented layers remain distinct:

1. `ClassWorldConfiguration` declares authoritative immutable class-world
   composition.
2. Class-world manifest JSON deterministically serializes configuration.
3. Manifest file transport moves manifest JSON at explicit local paths.
4. `ClassWorldReleaseDeclaration` records release identity and declared
   provenance.
5. Release-declaration serialization provides canonical JSON and strict parsing
   against the authoritative configuration.
6. Release-declaration file transport moves that JSON through explicit bounded
   local UTF-8 reads and atomic writes.
7. Release-declaration digest computation hashes canonical serialized
   declaration bytes.
8. In-memory declaration digest verification validates an expected digest,
   recomputes step 7, and compares the complete digest models.
9. File digest verification, implemented here, composes the reader from step 6
   with the verifier from step 8.
10. Future artifact and trust layers may inventory, assemble, archive, sign,
    attest, approve, publish, or deploy release content.

This contract implements only step 9. It adds no path, parsing, builder,
serialization, hashing, or comparison policy of its own.

## Composition contract version

The composition contract version is:

```python
SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION = (
    "0.1"
)
```

It is semantically distinct from the release-declaration schema, file-
transport, digest, and in-memory digest-verification contract versions. All are
currently `"0.1"`, but each versions a separate boundary.

## Public API

```python
from explore.packages import (
    compute_class_world_release_declaration_digest,
    verify_class_world_release_declaration_file_digest,
)

expected_digest = compute_class_world_release_declaration_digest(declaration)
result = verify_class_world_release_declaration_file_digest(
    "output/class-world.release.json",
    configuration,
    expected_digest,
)
```

The intentional public surface is:

- `verify_class_world_release_declaration_file_digest`;
- `ClassWorldReleaseDeclarationFileDigestVerificationResult`; and
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION`.

The function requires an explicit `str` or `pathlib.Path`, an authoritative
`ClassWorldConfiguration`, and a `ClassWorldReleaseDeclarationDigest`. There is
no default path, repository discovery, environment lookup, or bare digest-
string overload.

## Reader-first operation order

The v0.1 order is intentional:

1. call `read_class_world_release_declaration_file(path, configuration)` once;
2. if reading, parsing, or declaration building fails, return its declaration
   and three issue tuples directly with `verification=None`;
3. after a successful read, call
   `verify_class_world_release_declaration_digest(declaration, expected_digest)`
   once; and
4. return the reader's declaration and the verifier's result directly.

The existing reader remains authoritative for path validation, final-component
symlink rejection, regular-file enforcement, bounded reads, the byte limit,
UTF-8, BOM rejection, parsing, declaration building, and configuration
identity.

The existing in-memory verifier remains authoritative for expected-digest
validation, actual digest recomputation, complete digest-model comparison, and
mismatch behavior.

## Read-failure precedence

Reader failure takes precedence over malformed expected-digest input. If the
path cannot be read or the content cannot be parsed and built, the operation
returns the reader failure and does not invoke digest verification.

Expected-digest validation occurs only after a successful read. At that point,
the existing verifier's behavior is preserved without catching or translating
it:

- a wrong expected object type raises `TypeError`;
- a malformed algorithm or hexadecimal digest raises `ValueError`; and
- a well-formed unequal digest returns a normal result with `matches=False`.

These programmer-input errors are not file-transport issues.

## Immutable result and diagnostic preservation

`ClassWorldReleaseDeclarationFileDigestVerificationResult` is a frozen
dataclass containing exactly:

- `declaration`, the reader's declaration or `None`;
- `verification`, the verifier's result or `None`;
- `issues`, the reader's transport issue tuple;
- `serialization_issues`, the reader's parser issue tuple; and
- `declaration_issues`, the reader's builder issue tuple.

The composition layer does not translate, wrap, reorder, stringify, or combine
reader diagnostics. On success, it preserves the reader's declaration object,
including:

```python
result.declaration.configuration is configuration
```

The verification result preserves the exact supplied expected digest and
contains a freshly recomputed actual digest.

## Match and mismatch semantics

A successful matching read has a declaration, a verification result whose
`matches` value is `True`, and three empty reader issue tuples.

A valid mismatch is also a successful read. It returns the declaration and
both expected and actual digest models with `matches=False`; it does not create
a transport, serialization, or declaration issue.

## Canonical declaration, not raw file bytes

A match means the declaration represented by the file canonicalizes to the
supplied expected declaration digest. It does not mean the original file bytes
equal canonical serializer output.

For example, valid JSON with harmless whitespace or compact formatting may
parse to the same declaration. The existing digest API then serializes the
declaration canonically, so such a noncanonical input file can match the same
expected declaration digest even though its raw bytes differ.

This distinction does not weaken parser strictness. Invalid UTF-8, a leading
BOM, malformed JSON, duplicate keys, schema disagreement, and declaration-
builder failures remain reader failures.

## Read-only and purity boundary

File digest verification performs no:

- release-declaration writes, replacements, repairs, backups, or temporary-file
  creation;
- writer readback or changes to the existing writer;
- raw file hashing or independent serializer calls;
- package loading, validation, registration, inventory, or application;
- class-world assembly, runtime or Pygame work;
- network, database, Git, environment, clock, or randomness access; or
- result persistence, telemetry, or audit-record creation.

The only filesystem mutation in this workflow can come from a caller before or
after verification; the verification function itself is read-only.

## Security and trust boundary

A matching supplied digest does not establish:

- authenticity, signer identity, authority, approval, or publication status;
- the trustworthiness of the caller-provided expected digest;
- truth of engine, Student API, cohort, package, or repository provenance;
- package, asset, archive, manifest-file, runtime, or assembled-artifact
  integrity; or
- deployment state.

The v0.1 API introduces no HMAC, signature, key, certificate, trust store,
attestation, or trust-source policy.

## Deferred work

Only later contracts, if required, should define:

- raw release-file byte digests;
- artifact inventory and package or asset hashes;
- class-world assembly and archive hashing;
- signing, attestations, and trust-source policy;
- approval, publication, and deployment; and
- persistent audit records.
