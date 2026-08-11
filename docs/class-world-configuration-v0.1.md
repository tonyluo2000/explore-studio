# Immutable Class-World Configuration Model v0.1

> **Status:** Implemented pure in-memory configuration boundary. Deterministic
> JSON manifest serialization, parsing, and explicit local UTF-8 file transport
> are implemented separately. Immutable release identity and declared
> provenance are also implemented separately. Deterministic release-declaration
> digesting and pure in-memory digest verification are implemented separately.
> Class-world assembly, release artifacts, artifact hashing, signing,
> publication, approval, authentication,
> registries, and deployment remain deferred.

Immutable Class-World Configuration Model v0.1 describes what one class world
is intended to contain. It combines class-world identity and display metadata,
exact platform-version pins, minimal cohort metadata, exact ordered Explorer
Package pins, and one already validated `PackageSetPlan`.

```text
class-world identity and metadata
        +
engine and Student API version pins
        +
ordered exact package pins
        +
validated PackageSetPlan
        ↓
immutable ClassWorldConfiguration
```

This layer is pure. It neither discovers nor resolves inputs and it never
creates or mutates a runtime world.

## Configuration versus a release artifact

A `ClassWorldConfiguration` declares intended composition: identity, versions,
cohort metadata, package selection, and the validated registration plan.

A later release artifact may contain serialized manifests, generated files,
packaged assets, hashes, signatures, build provenance, or deployment metadata.
None of those belong to this model. The configuration does not prove artifact
integrity and is not itself a built class world.

Runtime application is a separate boundary too. Transactional package-set
application uses a `PackageSetPlan` and an explicit target to create Student API
runtime instances and mutate that target. Configuration construction does not
call application and does not inspect target capacity or state.

The downstream
[Serialized Class-World Manifest Schema v0.1](class-world-manifest-v0.1.md)
provides deterministic JSON serialization and strict parsing for this immutable
configuration. Parsing requires the matching validated `PackageSetPlan`; it
does not rebuild package composition or create a release artifact.
The further
[Class-World Manifest File Transport v0.1](class-world-manifest-file-transport-v0.1.md)
reads and atomically replaces manifest files at explicit local paths without
adding release-artifact semantics.
The downstream
[Class-World Release Identity and Provenance Model v0.1](class-world-release-identity-and-provenance-v0.1.md)
retains an exact configuration and derives immutable release identity and
declared provenance without producing an artifact. The separate
[Class-World Release Declaration Serialization v0.1](class-world-release-declaration-serialization-v0.1.md)
provides canonical JSON and strict parsing that requires this authoritative
configuration and rejects disagreement. The downstream
[Class-World Release Declaration File Transport v0.1](class-world-release-declaration-file-transport-v0.1.md)
moves that JSON through explicit bounded local UTF-8 reads and canonical atomic
replacement without reconstructing configuration. The separate
[Deterministic Class-World Release Declaration Digest v0.1](class-world-release-declaration-digest-v0.1.md)
identifies the canonical serialized declaration bytes without reading files or
authenticating an artifact. The separate
[Class-World Release Declaration Digest Verification v0.1](class-world-release-declaration-digest-verification-v0.1.md)
validates and compares expected and recomputed declaration digests without file
or artifact verification.

## Schema and identity

The only supported configuration schema version is exactly `"0.1"`, exposed as
`SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION`. The builder does not
infer a version, accept ranges, migrate older values, or normalize input.

The stable declared configuration identity for v0.1 is the pair:

```text
class_world_id + class_world_version
```

`class_world_id` follows the existing 1–64 character lower-kebab-case
identifier policy. `class_world_version` is an exact Semantic Versioning 2.0.0
value. No UUID, timestamp, hash, signature, or content-addressed identity is
generated. The pair identifies a declaration; it does not prove the integrity
of a later artifact.

`display_name` is preserved exactly as supplied. It must contain non-whitespace
text and may contain at most `CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH` (100)
characters. It is human-readable text and does not follow identifier syntax.

## Platform version pins

`engine_version` is a required exact Semantic Versioning 2.0.0 pin. The current
repository has no canonical runtime engine-version constant, so v0.1 validates
and preserves the pin but makes no claim that it matches a running engine.
Runtime verification belongs to a future builder or release verifier. The
implementation never reads `pyproject.toml` to discover a version.

`student_api_version` must be exactly `"0.1"`. The same exact value must appear
in the configuration specification, the supplied `PackageSetPlan`, every
selected package provenance value, and every nested registration-plan
provenance value. Unsupported or inconsistent plans are rejected; no migration
or adaptation occurs.

## Cohort metadata

`ClassWorldCohort` contains only:

- `cohort_id`, using the existing lower-kebab-case identifier policy; and
- `display_name`, preserved human-readable text of at most
  `COHORT_DISPLAY_NAME_MAX_LENGTH` (100) characters.

The model contains no dates, accounts, teacher details, student roster, or
individual student personal data.

## Exact ordered package pins

`ClassWorldConfigurationSpec.packages` is a non-empty tuple of
`ClassWorldPackagePin` values. Each pin contains a valid package ID and one
exact Semantic Version:

```python
(
    ClassWorldPackagePin("nova-character", "1.0.0"),
    ClassWorldPackagePin("crystal-lantern", "1.0.0"),
)
```

Caller order is significant and is never sorted, grouped, repaired, or
normalized. Duplicate identical pins and conflicting versions for one package
ID are both errors. Missing and extra pins are errors.

The specification pins are validation input only. The validated configuration
stores `package_set_plan` as the single canonical package and entry composition.
Its `packages` property derives a new immutable tuple of exact pins from that
plan. This avoids retaining two independently inconsistent sources of package
truth.

## Package-set agreement and defensive validation

The builder consumes one public `PackageSetPlan`; it never calls
`build_package_set_plan`. It requires exact index-by-index agreement for:

- package count;
- package order;
- package ID;
- exact package version;
- selected-package provenance;
- nested registration-plan provenance; and
- exact Student API version.

Because frozen public dataclasses can be manually constructed, the builder also
defensively confirms:

- non-empty tuple structure for packages, nested entries, and flattened
  entries;
- valid selected-package identity and exact version metadata;
- no duplicate selected package IDs;
- supported immutable registration entry types and values;
- entry provenance agreement;
- valid `package-id:contribution-id` qualified identities;
- no duplicate qualified identities;
- exact flattened-entry equality and order against nested plans; and
- Student API v0.1 aggregate cardinality of at most one character and one world
  object.

It does not rerun package validation, package loading, registration planning, or
package-set planning.

## Public API

```python
from explore.packages import build_class_world_configuration

result = build_class_world_configuration(spec, package_set_plan)
if result.is_configured:
    assert result.configuration is not None
    configuration = result.configuration
else:
    for issue in result.issues:
        print(issue.code, issue.location, issue.message)
```

The intentional public surface is:

- `build_class_world_configuration`;
- `ClassWorldConfigurationSpec`;
- `ClassWorldConfiguration`;
- `ClassWorldCohort`;
- `ClassWorldPackagePin`;
- `ClassWorldConfigurationResult`;
- `ClassWorldConfigurationIssue`;
- `ClassWorldConfigurationIssueCode`;
- `SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION`;
- `CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH`; and
- `COHORT_DISPLAY_NAME_MAX_LENGTH`.

All public models are frozen dataclasses. All public collections are tuples,
and successful configuration retains only validated immutable nested package
planning models. Repeated equivalent inputs produce equality-comparable
equivalent results.

## Diagnostics and atomicity

Issues have a stable code, message, structural location, and optional package
ID, package index, and field. Ordering is deterministic: input issues first;
world metadata in specification order; cohort fields; pins in caller order;
package-set consistency; then pin-to-plan agreement. Messages omit absolute
paths, raw exception representations, and unordered diagnostic output.

Construction is all-or-nothing. If any issue exists,
`ClassWorldConfigurationResult.configuration` is `None`; no partial metadata,
pin set, selected-package set, or entry set escapes as success. Inputs and all
external state remain unchanged.

## Safety and scope

Configuration construction performs no:

- filesystem reads, directory inspection, YAML parsing, or JSON parsing;
- serialization or output generation;
- hashing, signing, integrity calculation, or release-manifest work;
- package validation, loading, registration planning, or package-set planning;
- transactional single-plan or package-set application;
- target lookup, target mutation, or Student API runtime construction;
- `World`, `Character`, or `Object` creation;
- asset loading or materialization;
- Pygame initialization;
- Python code execution;
- network access or version resolution;
- global registry mutation; or
- package publishing, approval, authentication, or authorization.

## Implementation status and deferred work

- Explorer Package validation: implemented;
- declarative package loading: implemented;
- immutable single-package registration planning: implemented;
- transactional single-plan application: implemented;
- package-set preflight planning: implemented;
- transactional package-set application: implemented;
- immutable class-world configuration: implemented;
- serialized class-world manifest schema: implemented;
- explicit local UTF-8 manifest file transport: implemented;
- immutable release identity and declared provenance: implemented;
- deterministic release-declaration JSON serialization and strict parsing:
  implemented;
- explicit local UTF-8 release-declaration file transport: implemented;
- deterministic canonical release-declaration SHA-256 digest: implemented;
- pure in-memory release-declaration digest verification: implemented;
- class-world assembly: not implemented;
- release artifacts: not implemented;
- artifact hashing and signing: not implemented; and
- publication, approval, authentication, registries, and online services: not
  implemented.

Deferred work includes runtime engine-version verification, artifact hashing
and signing, class-world assembly, release packaging, approval and publication,
deployment, and persistent audit records.
