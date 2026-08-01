# Class-World Release Identity and Provenance Model v0.1

> **Status:** Implemented pure immutable in-memory release declaration.
> Release-declaration serialization and file transport, hashing, signing,
> class-world assembly, release artifacts, publication, and deployment remain
> deferred.

Class-World Release Identity and Provenance Model v0.1 declares which release
is intended and records the authoritative configuration and exact package pins
from which it is expected to be produced.

```text
immutable ClassWorldConfiguration
        +
explicit release ID and release version
        ↓
immutable ClassWorldReleaseDeclaration
```

The declaration records the exact configuration and package-version inputs
intended for a release. It does not verify assembled files or prove content
integrity.

## Architecture position

The implemented boundaries are distinct:

1. `ClassWorldConfiguration` is the validated in-memory declaration of the
   intended class world and its canonical `PackageSetPlan`.
2. The class-world manifest is deterministic JSON metadata for that
   configuration.
3. Manifest file transport moves manifest text through explicit caller-supplied
   local paths using strict UTF-8.
4. `ClassWorldReleaseDeclaration` identifies an intended release and records
   authoritative version and package inputs.
5. A future release artifact may contain assembled assets, copied or generated
   files, hashes, signatures, archives, publication metadata, or deployment
   metadata.

This model implements only step 4. It does not serialize or transport the
release declaration and does not assemble step 5.

## Public API

```python
from explore.packages import build_class_world_release_declaration

result = build_class_world_release_declaration(
    configuration,
    release_id="spring-showcase",
    release_version="1.0.0",
)

if result.is_built:
    assert result.declaration is not None
    declaration = result.declaration
else:
    for issue in result.issues:
        print(issue.code, issue.location, issue.message)
```

The intentional public surface is:

- `build_class_world_release_declaration`;
- `ClassWorldReleaseIdentity`;
- `ClassWorldReleaseProvenance`;
- `ClassWorldReleaseDeclaration`;
- `ClassWorldReleaseDeclarationResult`;
- `ClassWorldReleaseDeclarationIssue`;
- `ClassWorldReleaseDeclarationIssueCode`;
- `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION`; and
- `SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION`.

The only supported release-declaration contract version is exactly `"0.1"`.
The declaration also references the existing class-world manifest schema
version and the explicit manifest transport contract version, both exactly
`"0.1"`.

## Release identity

`ClassWorldReleaseIdentity` contains:

- `release_id`: an explicit caller-supplied lower-kebab-case identifier using
  the existing 1–64 character canonical identifier policy;
- `release_version`: an explicit caller-supplied exact Semantic Versioning
  2.0.0 value;
- `class_world_id`: derived exactly from the supplied configuration; and
- `class_world_version`: derived exactly from the supplied configuration.

The builder does not trim, normalize, coerce, infer, or increment these values.
It generates no UUID and derives no identifier or version from a timestamp.
Whitespace, path-like values, uppercase identifiers, underscores, malformed
Semantic Versions, Booleans, integers, bytes, and other non-string inputs are
not silently repaired.

The class-world identity fields are not separate builder arguments. Deriving
them from the configuration prevents callers from supplying conflicting copies.

## Declared provenance

`ClassWorldReleaseProvenance` records:

- the exact engine version from `ClassWorldConfiguration`;
- the exact Student API version from `ClassWorldConfiguration`;
- `SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION`;
- `SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION`;
- the exact cohort ID from `ClassWorldConfiguration`; and
- an immutable tuple of exact ordered `ClassWorldPackagePin` values derived
  from `ClassWorldConfiguration.package_set_plan`.

The existing package-pin model is reused. Package count, order, IDs, and exact
versions are preserved. The builder does not sort, deduplicate, resolve,
upgrade, load, validate, or plan packages. The complete supplied configuration
is retained by identity in the declaration, so
`declaration.configuration.package_set_plan` remains the canonical immutable
package and registration plan.

The declaration records declared provenance only. It contains no hashes,
signatures, file paths, checkout paths, usernames, machine names, environment
variables, host metadata, Git branch or commit, wall-clock timestamp, or other
mutable runtime state.

## Immutability and deterministic behavior

Identity, provenance, declaration, issue, and result models are frozen
dataclasses. Package pins and issues are tuples. The retained configuration and
its package-set plan are already immutable value graphs.

Equivalent ordered immutable inputs produce equal results. Package order
remains significant. The builder consults no clock, randomness source,
environment variable, filesystem, current working directory, Git state,
network, database, or global registry.

## Validation and diagnostics

The builder returns a complete declaration or `None`; no partial identity or
provenance escapes on failure. It validates in stable order:

1. configuration presence, runtime type, and existing configuration invariants;
2. release ID presence and identifier syntax; and
3. release version presence and exact Semantic Version syntax.

Because frozen public configuration models can be manually constructed, the
builder reuses the pure class-world configuration validation boundary. This
checks class-world metadata, engine and Student API versions, cohort metadata,
package-set structure, exact package order and pins, provenance agreement,
flattened entry order, duplicate identities, and Student API v0.1 cardinality.
It does not rebuild a package-set plan.

`None` produces `CONFIGURATION_REQUIRED`; a wrong runtime type produces
`CONFIGURATION_INVALID_TYPE`. A `ClassWorldConfiguration` subclass whose model
equality differs from the exact validated base model is rejected as
`CONFIGURATION_INVALID`, matching the existing defensive configuration and
manifest agreement policy.

Issues contain a stable code, message, and structural location such as
`release_id`, `release_version`, `configuration.class_world.id`, or
`configuration.package_set_plan.packages[0]`. Messages do not contain raw
exception representations, memory addresses, file paths, manifest contents, or
configuration dumps. Repeated equivalent failures produce equal issues in the
same order.

## Safety boundary

Release declaration construction performs no:

- JSON, YAML, or other serialization or parsing;
- release-declaration file reading or writing;
- class-world manifest reading, writing, serialization, or parsing;
- hashing, checksums, signing, key management, or integrity verification;
- package validation, loading, registration planning, or package-set planning;
- registration or package-set application;
- class-world assembly, asset copying, transformation, or archive creation;
- runtime `World`, `Character`, or `Object` construction or mutation;
- Pygame, renderer, scene, lifecycle, or event-loop initialization;
- network, cloud, database, online-storage, or registry access;
- publication, approval, authentication, authorization, or deployment; or
- persistent audit-record creation.

The declaration identifies an intended release declaration. It is not a built,
published, signed, verified, or deployed release artifact.

## Deferred work

Deferred work includes:

- release-declaration serialization and parsing;
- release-declaration file transport and any filename policy;
- class-world assembly and asset materialization;
- release artifact and archive creation;
- deterministic content hashing and integrity verification;
- signing, key management, and attestations;
- package approval and publication;
- authentication, authorization, and registry services;
- cloud or online storage and deployment; and
- persistent audit and recovery records.
