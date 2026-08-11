# Class-World Release Declaration Serialization v0.1

> **Status:** Implemented deterministic in-memory JSON serialization and strict
> parsing against an authoritative immutable `ClassWorldConfiguration`.
> Explicit bounded local file transport, deterministic digesting, and pure
> in-memory digest verification are implemented separately. Artifact hashing,
> signing, class-world assembly, release artifacts, publication, approval, and
> deployment remain deferred.

This contract gives the existing immutable `ClassWorldReleaseDeclaration` a
canonical JSON representation:

```text
immutable ClassWorldReleaseDeclaration
        ↓
canonical deterministic JSON serialization
        ↓
release declaration text

release declaration JSON text
        +
authoritative immutable ClassWorldConfiguration
        ↓
strict parsing and exact agreement validation
        ↓
existing pure release-declaration builder
        ↓
immutable ClassWorldReleaseDeclaration
```

The serialized declaration records intended release identity and
configuration-derived provenance. It does not verify artifact bytes or prove
provenance.

## Architecture position

The layers remain distinct:

1. `ClassWorldConfiguration` is the authoritative validated in-memory world
   declaration and retains the canonical `PackageSetPlan`.
2. The class-world manifest is deterministic JSON for that configuration.
3. Manifest file transport moves manifest text through explicit local paths
   using its own UTF-8, byte-size, and atomic-replacement policy.
4. `ClassWorldReleaseDeclaration` is immutable release identity and declared
   provenance derived from the authoritative configuration.
5. Release-declaration serialization is the deterministic JSON text contract
   documented here.
6. [Release-declaration file transport](class-world-release-declaration-file-transport-v0.1.md)
   moves this text across an explicit bounded local filesystem boundary.
7. [Release-declaration digesting](class-world-release-declaration-digest-v0.1.md)
   identifies the exact canonical serialized bytes with SHA-256.
8. [Release-declaration digest verification](class-world-release-declaration-digest-verification-v0.1.md)
   validates an expected digest, recomputes step 7, and compares the immutable
   digest models in memory.
9. [Release-declaration file digest verification](class-world-release-declaration-file-digest-verification-v0.1.md)
   composes step 6 reading with step 8 verification of the canonical
   declaration represented by the file, not its raw bytes.
10. A future release artifact may contain assembled files, assets, inventories,
   hashes, signatures, archives, and deployment metadata.

This layer implements only step 5. It does not reuse manifest file transport,
embed a class-world manifest, reconstruct configuration, rebuild a package-set
plan, or produce a release artifact.

## JSON schema

`SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION` is both the supported
in-memory release-declaration contract version and the JSON schema version. Its
only supported value is exactly `"0.1"`.

```json
{
  "schema_version": "0.1",
  "identity": {
    "release_id": "spring-showcase",
    "release_version": "1.0.0",
    "class_world_id": "expedition-orion-fall-2026",
    "class_world_version": "3.2.1"
  },
  "provenance": {
    "engine_version": "1.4.0",
    "student_api_version": "0.1",
    "class_world_manifest_schema_version": "0.1",
    "manifest_transport_contract_version": "0.1",
    "cohort_id": "expedition-orion",
    "packages": [
      {
        "id": "zeta-character",
        "version": "2.1.0-beta.1+class"
      },
      {
        "id": "alpha-lantern",
        "version": "1.0.0"
      }
    ]
  }
}
```

Every shown field is required. Every object has exactly the shown field set.
Identity, version, cohort, and package fields must be JSON strings; `identity`
and `provenance` must be objects; `packages` must be an array; and every package
entry must be an object. Values are never coerced, stripped, normalized, or
defaulted.

The text does not contain display names, a full class-world manifest, manifest
text, paths, Git metadata, timestamps, hashes, signatures, runtime state, or
generated metadata.

## Canonical serialization

`serialize_class_world_release_declaration` emits keys in schema order:

- root: `schema_version`, `identity`, `provenance`;
- identity: `release_id`, `release_version`, `class_world_id`,
  `class_world_version`;
- provenance: `engine_version`, `student_api_version`,
  `class_world_manifest_schema_version`,
  `manifest_transport_contract_version`, `cohort_id`, `packages`; and
- package: `id`, `version`.

Package array order is copied exactly from the declaration's retained
configuration. It is never sorted or deduplicated.

Canonical text uses JSON, two-space indentation, `ensure_ascii=False`, no key
sorting, no trailing spaces, no comments, no trailing commas, no byte-order
mark, and exactly one final newline. Equivalent declarations produce identical
text. Valid Unicode is emitted literally without normalization; identifier and
version fields remain governed by their existing model policies.

Before emitting JSON, the serializer rebuilds a declaration through
`build_class_world_release_declaration` using the retained configuration and
explicit release identity. Builder failure or inequality between the rebuilt
and supplied declaration raises `ValueError`; inconsistent values are never
repaired. A wrong declaration type raises `TypeError`.

## Strict parser API

```python
from explore.packages import parse_class_world_release_declaration

result = parse_class_world_release_declaration(
    declaration_text,
    configuration,
)
```

The supplied immutable `ClassWorldConfiguration` is authoritative. The parser
does not reconstruct one from JSON, rebuild a `PackageSetPlan`, or parse an
embedded class-world manifest.

After strict structural validation, the parser requires exact agreement for:

- class-world ID and version;
- engine version;
- Student API version;
- supported class-world manifest schema version;
- supported manifest transport contract version;
- cohort ID; and
- package count, array order, IDs, and exact versions.

Only after those checks pass does the parser call the existing pure builder
with the parsed release ID and version. The resulting declaration retains the
exact caller-supplied configuration instance:

```python
assert result.declaration is not None
assert result.declaration.configuration is configuration
```

The parser rejects malformed JSON, comments, trailing commas, `NaN`,
`Infinity`, `-Infinity`, non-object roots, duplicate keys, missing fields,
unknown fields, wrong exact JSON types, unsupported versions, and configuration
disagreement. Duplicate detection covers every object, including nested package
entries, before ordinary dictionaries could apply last-value-wins behavior.
Locations such as `identity.release_id` and
`provenance.packages[1].version` identify the duplicate structurally.

Insignificant whitespace, different object-key order, compact JSON, and
equivalent Unicode escapes are accepted when all schema and agreement rules
still pass. Package-array order remains significant.

## Results and diagnostics

`ClassWorldReleaseDeclarationParseResult` is a frozen dataclass containing:

- `declaration`, populated only on complete success;
- `issues`, an immutable tuple of
  `ClassWorldReleaseDeclarationSerializationIssue` values; and
- `declaration_issues`, an immutable tuple preserving existing
  `ClassWorldReleaseDeclarationIssue` builder diagnostics.

JSON, structure, version, or agreement failure leaves `declaration=None`, puts
diagnostics in `issues`, and leaves `declaration_issues=()`. When strict parsing
and agreement succeed but the builder rejects the release identity or a
manually inconsistent configuration, `issues=()` and the builder's issues are
preserved in `declaration_issues`. No partial declaration is returned.

Serialization issues contain a stable enum code, privacy-safe message, and
structural location. Ordering is deterministic: text and JSON errors first,
then root, identity, provenance, package agreement, and finally separately
preserved builder issues. Messages include no full input text, configuration
dump, raw exception representation, file path, or memory address.

## Round trips

For every valid declaration:

```python
text = serialize_class_world_release_declaration(declaration)
parsed = parse_class_world_release_declaration(text, declaration.configuration)

assert parsed.declaration == declaration
assert parsed.declaration is not None
assert parsed.declaration.configuration is declaration.configuration
assert serialize_class_world_release_declaration(parsed.declaration) == text
```

Valid noncanonical JSON parses to the same immutable declaration and then
serializes to canonical text.

## Determinism and safety boundary

Serialization and parsing are pure in-memory operations. They consult no clock,
randomness source, UUID generator, environment variable, current directory,
filesystem metadata, Git state, network, database, registry, or mutable global
state. They perform no file I/O, package validation or loading, registration or
package-set planning, package-set application, runtime construction, Pygame
initialization, student-code execution, asset copying, assembly, publication,
approval, or deployment.

This serialization contract itself defines no release-declaration filename,
byte-size limit, BOM transport policy, encoding, or atomic replacement
behavior. Those belong to the separate
[Class-World Release Declaration File Transport v0.1](class-world-release-declaration-file-transport-v0.1.md).
Serialization creates no hash, signature, integrity proof, inventory, archive,
or persistent audit record. The separate
[Deterministic Class-World Release Declaration Digest v0.1](class-world-release-declaration-digest-v0.1.md)
hashes this serializer's exact final-newline-terminated UTF-8 output. The
[Class-World Release Declaration Digest Verification v0.1](class-world-release-declaration-digest-verification-v0.1.md)
reuses that digest API rather than serializing or hashing independently.

## Deferred work

Deferred work includes:

- stale-temporary-file recovery and concurrent-writer coordination;
- verified declaration-file readback and file-digest comparison;
- assembled-artifact hashing and integrity verification;
- artifact inventory and archive creation;
- class-world assembly and asset materialization;
- signing, key management, and attestations;
- approval and publication;
- authentication, authorization, registries, and online storage;
- deployment; and
- persistent audit and recovery records.
