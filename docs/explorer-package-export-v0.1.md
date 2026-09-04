# Deterministic Explorer Package Export v0.1

> **Status:** Implemented local export of one validated, declarative Explorer
> Package. Publishing, approval, authentication, registries, signing,
> deployment, and student-code execution remain outside this contract.

The `explore-package` platform command exposes two local operations:

```bash
explore-package validate /absolute/package-root --json
explore-package export /absolute/package-root \
  --output /absolute/dist/{package-id}-{version}.explorer-package.zip --json
```

Relative CLI paths are resolved before calling the platform API. The public
`export_explorer_package` API itself requires an explicit absolute package root
and destination. The destination parent must exist, the destination must be
absent, and the filename is derived from the validated package ID and version.

## Artifact contract

The ZIP contains only `manifest.yaml`, declared contributions in manifest order,
and declared assets in manifest order. Undeclared repository files are excluded.
Members use ZIP `STORED`, timestamp `1980-01-01 00:00:00`, Unix creator system,
regular-file mode `0644`, and empty extra fields and comments. The archive has no
comment. Equivalent input bytes therefore produce byte-identical archives.

Immutable export metadata records the package ID, package version, Student API
version, ordered member paths, per-member byte counts and SHA-256 digests,
aggregate content bytes, complete archive byte count, and SHA-256 over the raw
archive bytes. Stable compact JSON is available from the API and `--json`.

## Validation and safety

Export reuses Explorer Package v0.1 validation and declarative loading. It then
reads the manifest and declared files through descriptor-relative
`O_DIRECTORY | O_NOFOLLOW` traversal. Reads are bounded to 64 MiB per member and
256 MiB aggregate. Two snapshots around validation/loading must match exactly;
changes, symbolic links, aliases, non-regular files, and size violations fail
before the destination is created. The completed ZIP is published atomically to
an absent destination through an operation-owned sibling staging file.

This is a local artifact-creation boundary. It never imports or executes student
code, contacts a network, publishes, approves, registers, signs, or deploys a
package. A Git commit records source history; an export creates a local package
candidate; future publishing is a separate trusted workflow.
