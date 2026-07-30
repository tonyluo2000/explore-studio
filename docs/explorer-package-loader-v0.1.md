# Local Explorer Package Loader v0.1

> **Status:** Implemented local prototype. This document defines the
> declarative contribution shapes accepted by the v0.1 loader.

The Local Explorer Package Loader consumes one already-unpacked Explorer
Package directory, runs the package validator, and returns immutable typed
contributions. It is a pure local parse-and-return boundary: it does not
register contributions with an engine, assemble a class world, publish a
package, contact a network service, or execute student Python.

## Validation-first flow

```text
package directory
       |
       v
validate_explorer_package(...)
       |
       +-- invalid --> validation issues; no contribution files read
       |
       v
read declared contribution YAML in manifest order
       |
       +-- any issue --> loading issues; no partial package returned
       |
       v
immutable LoadedExplorerPackage
```

Package validation is a hard gate. Only validator-approved declaration paths
are read. Contribution loading is atomic: valid contributions are not returned
when another contribution in the same package has a loading issue.

## Character contribution

A `character` declaration points to a strict YAML mapping with these fields:

```yaml
name: "Nova"          # required nonblank text
x: 430                # optional nonnegative integer; default 430
y: 270                # optional nonnegative integer; default 270
color: "gold"         # optional Student API colour name; default "gold"
asset_id: "portrait"  # optional manifest-declared image asset ID
```

This shape maps directly to Student API v0.1 character configuration. The
engine supplies character dimensions and movement speed, so dimensions,
movement, speed, behavior, dialogue, and code hooks are not accepted fields.
An asset is optional because the Student API has a color-based default
appearance.

## World-object contribution

A `world_object` declaration points to a strict YAML mapping with these fields:

```yaml
name: "Crystal Lantern"                  # required nonblank text
x: 120                                   # required nonnegative integer
y: 460                                   # required nonnegative integer
color: "yellow"                          # optional; default "brown"
asset_id: "lantern-image"                # optional declared image asset ID
when_near: "The lantern glows warmly."   # optional nonblank text
when_interacted: "A crystal spark!"      # optional nonblank text
```

This shape maps to the Student API v0.1 object configuration and its two
message-based interactions. The engine supplies fixed object dimensions.
Width, height, collision bounds, solidity, callbacks, decorators, commands,
and arbitrary behavior hooks are not accepted.

## Values and strict fields

Names and interaction messages must be strings containing non-whitespace text;
their outer whitespace is removed. Coordinates are integers of zero or greater.
Booleans are not coordinates, and floats—including NaN and infinity—are
rejected. Colors use the exact Student API v0.1 named-color vocabulary.

Unknown fields are errors. The loader does not silently accept misspellings or
retain untyped extension data. For each contribution, issues follow the field
order shown above, followed by unknown field names in sorted order.
Contribution groups follow manifest order.

Contribution files must be UTF-8 YAML mappings. They are parsed with
`yaml.safe_load`. Empty documents, non-mapping roots, malformed YAML, unsafe
YAML tags, nested values where scalars are required, and incorrect scalar types
produce structured issues rather than ordinary content exceptions.

## Asset references

`asset_id` resolves against the package manifest. The referenced asset must
exist in the manifest and have type `image`; audio cannot be used as a visual
appearance. The typed result retains the asset ID, type, and validator-approved
package-relative path. It does not use a machine-specific absolute path as
asset identity.

The loader does not decode PNG images or WAV audio, create Pygame objects, or
initialize a display or sound system.

## Public API

```python
from explore.packages import load_explorer_package

result = load_explorer_package(
    "examples/explorer-packages/nova-character"
)

if result.is_loaded:
    package = result.package
    assert package is not None
    for character in package.characters:
        print(character.qualified_id, character.name)
else:
    for issue in result.all_issues:
        print(f"{issue.code}: {issue.location}: {issue.message}")
```

`load_explorer_package` accepts a string or path-like package directory and
returns `PackageLoadResult`. Its public immutable value objects are:

- `PackageLoadResult`, containing the original `ValidationReport`, an optional
  fully loaded package, and loading issues;
- `LoadedExplorerPackage`, containing package metadata, compatibility,
  provenance, manifest-order contributions, and declared asset references;
- `LoadedCharacter` and `LoadedWorldObject`;
- `PackageProvenance`, containing package ID, package version, and exact
  Student API version;
- `PackageAssetReference`; and
- `PackageLoadIssue`, with a stable `PackageLoadIssueCode`, message, and
  package-relative location.

Each contribution has its manifest-local `contribution_id`, a future-facing
`package-id:contribution-id` qualified identity, its declaration source path,
and package provenance. Duplicate output is guarded within one load. Resolving
identities across packages remains a later registry or class-world concern.

## Safety boundary

The loader reads only the validator-approved local manifest and declared
contribution files. It has no network behavior and performs no dependency
resolution. It never imports package modules, invokes package commands, runs
package tests, uses `eval` or `exec`, or interprets YAML as Python. A local Git
commit is still not publication, and successful local loading is neither
approval nor class-world inclusion.

## Examples and implementation status

Both checked-in examples load through this API:

- [`nova-character`](../examples/explorer-packages/nova-character/) produces a
  `LoadedCharacter`;
- [`crystal-lantern`](../examples/explorer-packages/crystal-lantern/) produces
  a `LoadedWorldObject` with interaction messages.

Package contract validation and local declarative loading are implemented.
Engine or Student API registration adapters, cross-package namespace policy,
class-world assembly, archive loading, online publishing and approval, schema
migration, semantic-version ranges, dependencies, and executable extensions
remain deferred.
