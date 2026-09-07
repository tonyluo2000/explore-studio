# Explorer Package Contract v0.2

> **Status:** Implemented additive local schema contract.

Explorer Package v0.2 preserves every v0.1 field and validation rule and adds
optional package-local named toggle styles. Student API compatibility remains
exactly `"0.1"`.

## Named toggle styles

A v0.2 manifest may declare:

```yaml
schema_version: "0.2"

toggle_styles:
  - id: "portal-switch"
    off_color: "red"
    on_color: "green"
```

Each entry has exactly `id`, `off_color`, and `on_color`. IDs use the existing
lower-kebab-case identifier contract and are unique within one package. The two
colors are nonblank supported Student API v0.1 color names and must differ.
The same style ID may independently occur in another package.

A world object may use either its existing inline `toggle` mapping or one
unqualified package-local reference:

```yaml
name: "North Switch"
x: 120
y: 220
toggle_style_id: "portal-switch"
```

`toggle_style_id` is mutually exclusive with inline `toggle`, `color`, and
`asset_id`. It must resolve exactly once in the declaring package. Malformed,
qualified, unknown, or cross-package references fail closed.

The validator validates the style table before contribution parsing. The local
loader resolves each reference into the existing immutable
`LoadedWorldObjectToggle(off_color, on_color)` and retains immutable bounded
provenance `(package_id, style_id, referencing_object_ids)`. Registration,
package-set planning, configuration, and Classroom Trail receive the resolved
toggle model; runtime performs no style lookup and gains no new behavior.

Schema v0.1 remains accepted unchanged and does not accept `toggle_styles` or
`toggle_style_id`. Validators that support only v0.1 reject schema v0.2 rather
than interpreting it partially. Unknown schema versions fail closed.

Generic variables, templates, inheritance, executable configuration,
cross-package style references, and runtime style lookup are not part of v0.2.
