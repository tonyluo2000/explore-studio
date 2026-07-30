# Explorer Package Contract v0.1

> **Status:** Implemented prototype. This document defines the current validator
> contract; it does not freeze future package versions.

Explorer Package v0.1 is the declarative boundary between an independently owned
student repository and future shared-world assembly. The prototype validates an
unpacked package directory. It does not publish, approve, load, or execute a
contribution.

## Package layout

Every package has `manifest.yaml` at its root. Other directories are optional and
exist only when referenced by a declaration:

```text
explorer-package/
├── manifest.yaml
├── character/
├── objects/
└── assets/
```

The checked-in examples are under
[`examples/explorer-packages/`](../examples/explorer-packages/).

## Manifest shape

The complete v0.1 shape is:

```yaml
schema_version: "0.1"

package:
  id: "nova-character"
  display_name: "Nova the Explorer"
  version: "1.0.0"

compatibility:
  student_api: "0.1"

contributions:
  - id: "nova"
    type: "character"
    path: "character/nova.yaml"

assets:
  - id: "nova-avatar"
    type: "image"
    path: "assets/nova.png"
```

`assets` is optional. All other top-level fields are required, and
`contributions` must contain at least one declaration. Unknown fields are
rejected so spelling mistakes do not become ignored configuration.

This refines the earlier non-normative architecture example to the smallest
contract supported by Student API v0.1. Author identity, engine compatibility,
dependencies, attribution, integrity hashes, capabilities, compatibility ranges,
and package entry-point execution remain deferred. They are not accepted as
v0.1 fields.

## Identifiers and versions

Package, contribution, and asset IDs:

- contain 1–64 characters;
- begin with a lowercase ASCII letter;
- use only lowercase ASCII letters, digits, and hyphens;
- do not contain consecutive hyphens; and
- do not end in a hyphen.

Examples include `nova-character`, `crystal-lantern`, and `river-rescue`.
Contribution IDs are unique within a package's contribution namespace. Asset IDs
are unique within its asset namespace. Class-wide namespace and registry
collision handling are deferred.

`package.display_name` is display text, not an identifier. It must be a string,
must contain non-whitespace text, and may contain at most 100 characters, as
defined by `DISPLAY_NAME_MAX_LENGTH`. The value is retained as supplied and is
not subject to the lower-kebab-case identifier rules.

Package versions use Semantic Versioning 2.0.0. Student API compatibility is an
exact version in this prototype; the only supported value is `"0.1"`.

## Contributions

Contract v0.1 supports only the declarative concepts implemented by Student API
v0.1:

| Type | File formats |
|------|--------------|
| `character` | `.yaml`, `.yml` |
| `world_object` | `.yaml`, `.yml` |

The validator confirms declaration structure, identifier uniqueness, supported
type, path safety, file extension, existence, and regular-file status. It does
not yet interpret the contents of character or world-object YAML files.

## Assets

Assets are explicit declarations. Undeclared files are not loaded or inspected.
The prototype policy is:

| Type | Allowed extension |
|------|-------------------|
| `image` | `.png` |
| `audio` | `.wav` |

Each declared asset must have a unique ID and normalized path, exist as a regular
file, and be no larger than `5,242,880` bytes (5 MiB). The implementation exposes
this default as `MAX_ASSET_SIZE_BYTES`. These extensions and size limits are
conservative prototype defaults, not permanent platform policy. Media metadata
is not inspected or transformed.

Contribution and asset extension validation is case-insensitive, so `.yaml`,
`.yml`, `.png`, and `.wav` accept case variants such as `.YAML` and `.PNG`. The
declared path is still resolved exactly as written against the filesystem; the
validator does not perform case-insensitive filename lookup. Portable package
authors should use lowercase filenames and extensions.

## Filesystem and execution safety

Declared paths use portable forward-slash relative paths. Validation rejects:

- empty or absolute paths;
- Windows drive paths and backslash paths;
- `..` parent traversal;
- canonical paths outside the package root;
- duplicate normalized paths;
- missing or non-regular files; and
- a symlink at any declared path component.

The validator reads only `manifest.yaml`, using `yaml.safe_load`. It never imports
student modules, executes Python, evaluates expressions, installs dependencies,
runs package tests or commands, follows remote references, or processes assets.
A declared `.py` contribution is inert and rejected as an unsupported file type.
Safe execution of arbitrary student Python remains a separate, deferred security
design.

## Public validation API

```python
from explore.packages import validate_explorer_package

report = validate_explorer_package(
    "examples/explorer-packages/nova-character"
)

if report.is_valid:
    print(report.manifest.package.display_name)
else:
    for issue in report.issues:
        print(f"{issue.code}: {issue.location}: {issue.message}")
```

`ValidationReport`, its parsed manifest models, and `ValidationIssue` are
immutable value objects. Each issue has a stable `code`, actionable `message`,
and manifest-relative `location`. Identical package contents produce issues in
the same order, without machine-specific absolute paths in normal diagnostics.

The validator operates only on local, already-unpacked directories. Archive
formats, publishing, authentication, approval, registries, and class-world
assembly are outside this prototype.
