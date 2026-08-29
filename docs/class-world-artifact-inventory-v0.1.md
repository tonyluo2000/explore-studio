# Class-World Package Artifact Inventory v0.1

> **Status:** Implemented pure in-memory inventory construction from one
> successfully verified release declaration and exact content-addressed
> Explorer Package artifact declarations. Artifact reads, artifact hashing,
> assembly, execution, signing, approval, publication, and deployment remain
> deferred.

Package Artifact Inventory v0.1 answers one narrow question:

> Does this complete set of package artifact declarations correspond exactly
> to the package pins in this successfully verified release declaration, and
> if so, what is their canonical release order?

```text
matching release-declaration file digest verification result
        +
immutable tuple of package artifact declarations
        ↓
validate declaration shape and SHA-256 digest syntax
        ↓
join declarations to exact verified package ID/version pins
        ↓
canonicalize to release package-pin order
        ↓
immutable ClassWorldArtifactInventory
```

## Scope and architecture position

This contract is the first artifact-composition primitive after verified
release-declaration file readback. It produces no files and performs no
assembly. It retains only:

- the exact verified `ClassWorldReleaseDeclaration`;
- the already-recomputed matching declaration digest; and
- one package artifact declaration for each exact package pin, in release pin
  order.

The package artifact declaration contains `package_id`, `package_version`,
`digest_algorithm`, and `digest_hex`. In v0.1 the algorithm is exactly
`"sha256"` and the digest is exactly 64 lowercase hexadecimal characters.
The digest is caller-supplied content identity; this layer validates its
representation but does not read or hash the artifact.

Student repositories remain outside the inventory. Each inventory entry names
one independently versioned Explorer Package artifact and never expands,
copies, merges, imports, or executes its contents.

## Public API

```python
from explore.packages import (
    ClassWorldPackageArtifactDeclaration,
    build_class_world_artifact_inventory,
)

result = build_class_world_artifact_inventory(
    verified_release_declaration,
    (
        ClassWorldPackageArtifactDeclaration(
            package_id="alice-fox",
            package_version="1.2.0",
            digest_algorithm="sha256",
            digest_hex="...64 lowercase hexadecimal characters...",
        ),
    ),
)
```

The public contract includes:

- `build_class_world_artifact_inventory`;
- `ClassWorldPackageArtifactDeclaration`;
- `ClassWorldArtifactInventory` and `ClassWorldArtifactInventoryResult`;
- `ClassWorldArtifactInventoryIssue` and its stable issue-code enum;
- `SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION`; and
- `SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM`.

Both contract constants are currently `"0.1"` and `"sha256"`, respectively.

## Verified-input gate

The upstream input must be the exact existing file-digest-verification result
type and must contain:

- a release declaration;
- no file, serialization, or declaration issues;
- an in-memory digest verification result;
- `matches is True`; and
- equal expected and actual declaration digest models.

Missing, wrong-type, failed, mismatching, or internally inconsistent upstream
results fail before artifact declarations are inspected. The inventory layer
does not reread the declaration file, reparse JSON, reserialize the
declaration, or recompute its digest.

## Artifact declaration rules

The caller supplies an immutable tuple. Every entry must be the exact artifact
declaration model type with:

- a valid Explorer Package identifier;
- a semantic package version;
- digest algorithm exactly `"sha256"`; and
- a 64-character lowercase hexadecimal digest.

The declarations must form a one-to-one join with the verified release's
package pins:

- every pinned package has exactly one declaration;
- no unpinned package is accepted;
- a declaration version exactly equals its corresponding pin; and
- a package ID cannot appear twice.

Any issue makes the result atomic: `inventory` is `None` and every diagnostic
is returned in deterministic inspection order. Valid caller declaration order
does not affect output; successful inventories always follow the authoritative
release package-pin order.

Two distinct packages may intentionally have the same content digest. Package
identity, not digest equality, defines duplication because identical bytes can
be valid independent package artifacts.

## Purity and deferred work

Inventory construction performs no filesystem, network, database, Git,
environment, clock, randomness, Pygame, subprocess, or student-code operation.
It does not load an Explorer Package or apply a package-set registration plan.

Later contracts may define artifact-file digest verification, artifact
resolution, deterministic class-world assembly, archive construction and
hashing, attribution output, signing or attestation, approval, publication,
and deployment. Those concerns are deliberately absent here.
