# Serialized Class-World Manifest Schema v0.1

> **Status:** Implemented deterministic in-memory JSON serialization and strict
> parsing. Explicit local UTF-8 file transport is implemented separately.
> Immutable release identity and declared provenance are implemented separately.
> Release-declaration serialization and file transport, class-world assembly,
> release artifacts, hashing, signing, publication, approval, authentication,
> registries, and online services remain deferred.

Serialized Class-World Manifest Schema v0.1 gives an immutable
`ClassWorldConfiguration` a deterministic, portable JSON declaration. It
preserves class-world metadata, exact platform pins, cohort metadata, and exact
ordered Explorer Package pins. It contains no runtime objects or generated
assets.

```text
immutable ClassWorldConfiguration
        ↓
deterministic JSON serialization
        ↓
class-world manifest text

class-world manifest text + validated PackageSetPlan
        ↓
strict JSON and configuration validation
        ↓
immutable ClassWorldConfiguration
```

JSON is the only v0.1 format. The Python standard library provides strict
scalar handling and deterministic output without another dependency. YAML and
interchangeable format negotiation are not part of this schema.

## Configuration, manifest, and release artifact

An immutable `ClassWorldConfiguration` is the validated in-memory declaration.
Its `PackageSetPlan` remains the canonical package and registration
composition.

A serialized class-world manifest is portable JSON metadata plus ordered exact
package pins. The pins are sufficient because parsing requires the caller to
supply the matching already validated `PackageSetPlan`. A manifest is not a
release artifact and does not rebuild a plan.

A future release artifact may include generated files, packaged assets, hashes,
signatures, lock data, build provenance, or deployment metadata. This layer
creates none of those. The recommended filename for the implemented explicit
local file transport is:

```text
class-world.manifest.json
```

This schema API continues to operate on Unicode `str` values only. The separate
[Class-World Manifest File Transport v0.1](class-world-manifest-file-transport-v0.1.md)
provides explicit-path bounded reads, strict UTF-8 without BOM, and canonical
same-directory atomic replacement. It delegates JSON semantics back to this
layer and does not turn the manifest into a release artifact.
The further
[Class-World Release Identity and Provenance Model v0.1](class-world-release-identity-and-provenance-v0.1.md)
records explicit release identity and declared provenance from the exact
configuration. It does not serialize the release declaration or verify artifact
bytes.

## Schema

The only supported manifest schema version is exactly `"0.1"`.

```json
{
  "schema_version": "0.1",
  "class_world": {
    "id": "expedition-orion-fall-2026",
    "display_name": "Expedition Orion — Fall 2026",
    "version": "1.0.0"
  },
  "engine_version": "1.0.0",
  "student_api_version": "0.1",
  "cohort": {
    "id": "expedition-orion",
    "display_name": "Expedition Orion"
  },
  "packages": [
    {
      "id": "nova-character",
      "version": "1.0.0"
    },
    {
      "id": "crystal-lantern",
      "version": "1.0.0"
    }
  ]
}
```

All shown fields are required; the parser supplies no defaults. String fields
must be JSON strings, `class_world` and `cohort` must be objects, `packages`
must be an array, and each package item must be an object containing string
`id` and `version` fields. Numbers, Booleans, arrays, objects, and `null` are
not coerced into strings.

Unknown fields are rejected at the root, inside `class_world`, inside `cohort`,
and inside every package item. Duplicate keys are also rejected at every object
level. The decoder retains object pairs long enough to identify nested
locations such as `class_world.id`, `cohort.display_name`, and
`packages[1].version`; it never accepts Python's default last-key-wins behavior.
Malformed JSON, comments, trailing commas, `NaN`, `Infinity`, and
`-Infinity` are invalid.

The package array order is significant. Its count, package ID, and exact
Semantic Version must match `PackageSetPlan.packages` index by index. Parsing
does not sort, infer, resolve, omit, or repair package pins.

Display names retain leading and trailing whitespace exactly. The existing
configuration builder still requires nonblank text and enforces its maximum
length; serialization and parsing do not trim, normalize, collapse, or rewrite
valid display text.

## Canonical JSON

`serialize_class_world_manifest` emits:

- standard JSON with double quotes;
- literal Unicode text through `ensure_ascii=False`;
- two-space indentation;
- no comments, trailing commas, trailing spaces, or non-finite numbers;
- exactly one newline after the closing brace; and
- no generated metadata.

Keys use schema order rather than lexical sorting. Root order is
`schema_version`, `class_world`, `engine_version`, `student_api_version`,
`cohort`, `packages`. Class-world order is `id`, `display_name`, `version`;
cohort order is `id`, `display_name`; package order is `id`, `version`.
Package array order comes directly from the configuration's canonical
`PackageSetPlan`.

Equivalent configurations therefore produce exactly equal text. The parser may
accept different insignificant whitespace, object-key order, or equivalent
Unicode escaping, but reserialization always produces this canonical form.

## Public API

```python
from explore.packages import (
    parse_class_world_manifest,
    serialize_class_world_manifest,
)

manifest_text = serialize_class_world_manifest(configuration)
result = parse_class_world_manifest(
    manifest_text,
    configuration.package_set_plan,
)
```

`serialize_class_world_manifest(configuration)` returns `str`. Passing the
wrong model type raises a stable `TypeError`. A manually inconsistent public
configuration raises `ValueError` after defensive validation through
`build_class_world_configuration`; invalid JSON is never emitted.

`parse_class_world_manifest(manifest_text, package_set_plan)` returns an
immutable `ClassWorldManifestParseResult`. Its `configuration` is populated
only when parsing, structure checks, package agreement, and configuration
validation all succeed. Otherwise it is `None` and `issues` is an immutable
tuple of `ClassWorldManifestIssue` values with a stable
`ClassWorldManifestIssueCode`, message, and structural location.

Configuration-builder diagnostics are not discarded. Pin count, order, ID,
and version mismatches receive specific manifest issue codes. Other builder
diagnostics are retained as `CONFIGURATION_INVALID` issues whose messages name
the original configuration issue code and preserve its explanation. Locations
from configuration input are translated to manifest field names where
applicable; package-set-plan defects retain their plan locations.

## Round trip

For every valid configuration:

```python
text_one = serialize_class_world_manifest(configuration)
parsed = parse_class_world_manifest(text_one, configuration.package_set_plan)

assert parsed.configuration == configuration
assert parsed.configuration is not None

text_two = serialize_class_world_manifest(parsed.configuration)
assert text_two == text_one
```

The supplied plan is retained as the configuration's canonical composition.
Parsing never validates packages, reads package sources, loads declarations,
builds registration plans, or rebuilds a package-set plan.

## Safety boundary and deferred work

Manifest serialization and parsing perform no filesystem I/O, YAML parsing,
hashing, signing, network access, package validation, package loading,
registration planning, package-set planning, transactional application, target
inspection, runtime object construction, asset materialization, Pygame
initialization, publication, approval, authentication, or deployment. They do
not assemble a class world or generate a release artifact.

Deferred work includes release-declaration serialization and file transport,
deterministic artifact hashing, signing, class-world assembly, release
packaging, publication and approval, deployment, persistent audit records,
registry services, target locking, and persistent recovery.
