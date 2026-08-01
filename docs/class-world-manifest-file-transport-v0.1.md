# Class-World Manifest File Transport v0.1

> **Status:** Implemented explicit local UTF-8 file transport. Immutable
> configuration and deterministic JSON manifest semantics are implemented in
> separate layers. Immutable release identity and declared provenance are also
> implemented separately. Deterministic release-declaration JSON serialization
> and strict parsing are implemented separately. Release-declaration file
> transport, hashing, signing, class-world assembly, release artifacts,
> publication, approval, authentication, registries, online storage, and
> deployment are not implemented.

Class-World Manifest File Transport v0.1 moves deterministic class-world
manifest text across one explicit local filesystem boundary:

```text
immutable ClassWorldConfiguration
        ↓
canonical manifest serialization
        ↓
strict UTF-8 encoding
        ↓
same-directory temporary file
        ↓
atomic local-file replacement
```

```text
explicit local manifest path
        ↓
bounded binary read
        ↓
strict UTF-8 decoding
        ↓
existing strict manifest parser + validated PackageSetPlan
        ↓
immutable ClassWorldConfiguration
```

The recommended filename is:

```text
class-world.manifest.json
```

It is a recommendation, not an API default. Every read and write requires a
caller-supplied `str` or `pathlib.Path`. The transport never infers a path from
the current working directory, a package or repository root, an environment
variable, a user home directory, or global configuration. A caller may choose
another filename or an explicit relative path.

## Layer boundaries

An immutable `ClassWorldConfiguration` is the validated in-memory declaration.
Its `PackageSetPlan` remains the canonical package and registration composition.

A class-world manifest is deterministic JSON `str` metadata. Serialization and
strict parsing belong to
[Serialized Class-World Manifest Schema v0.1](class-world-manifest-v0.1.md), not
to this filesystem layer.

File transport encodes, reads, writes, and replaces only that manifest text. A
transported manifest is not a release artifact. A future release artifact may
include packaged assets, generated files, hashes, signatures, deployment
metadata, or release provenance; this transport creates none of those. The
[Class-World Release Identity and Provenance Model v0.1](class-world-release-identity-and-provenance-v0.1.md)
records declared release inputs in memory without reusing this file transport.

## Public API

```python
from explore.packages import (
    read_class_world_manifest_file,
    write_class_world_manifest_file,
)

write_result = write_class_world_manifest_file(
    configuration,
    "output/class-world.manifest.json",
)

read_result = read_class_world_manifest_file(
    "output/class-world.manifest.json",
    configuration.package_set_plan,
)
```

The intentional public surface is:

- `read_class_world_manifest_file`;
- `write_class_world_manifest_file`;
- `ClassWorldManifestFileReadResult`;
- `ClassWorldManifestFileWriteResult`;
- `ClassWorldManifestFileIssue`;
- `ClassWorldManifestFileIssueCode`; and
- `MAX_CLASS_WORLD_MANIFEST_BYTES`; and
- `SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION`.

The transport policy is explicitly versioned as `"0.1"` through
`SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION`. The release
provenance model references this constant; it does not infer a contract version
from the recommended filename.

All result and issue models are frozen dataclasses. Issue collections and
preserved manifest-issue collections are tuples. No result exposes a file
handle, mutable runtime object, or private temporary-file path.

`None`, empty strings, and whitespace-only strings produce `PATH_REQUIRED`.
Bytes paths and objects other than `str` or `Path` produce
`PATH_INVALID_TYPE`. Whitespace in an otherwise usable path is not stripped or
normalized. Wrong configuration types retain
`serialize_class_world_manifest`'s `TypeError` contract. An invalid manually
constructed `ClassWorldConfiguration` produces a structured `MANIFEST_INVALID`
write issue and leaves the destination unchanged.

## UTF-8 and byte-size contract

Manifest files use strict UTF-8 without a byte-order mark. Reading rejects:

- malformed UTF-8 and truncated multibyte sequences;
- UTF-16 or UTF-32 byte streams that are not valid UTF-8; and
- a UTF-8 BOM, reported as `MANIFEST_BOM_NOT_ALLOWED`.

Writing calls `str.encode("utf-8", errors="strict")` and never emits a BOM.
Valid Unicode text, including leading and trailing display-name whitespace,
remains unchanged.

The named v0.1 limit is:

```python
MAX_CLASS_WORLD_MANIFEST_BYTES = 1 * 1024 * 1024
```

The limit is measured in encoded UTF-8 bytes, not Unicode characters. A reader
requests at most `MAX_CLASS_WORLD_MANIFEST_BYTES + 1` bytes in one bounded
read. Seeing the extra byte produces `FILE_TOO_LARGE` without reading an
arbitrarily large file into memory or invoking JSON parsing. Exactly 1 MiB
continues through decoding and parsing. A writer encodes canonical text before
checking the limit; oversized output creates no temporary file and does not
replace an existing destination.

## Read contract

`read_class_world_manifest_file(path, package_set_plan)` requires one explicit
local path and one immutable `PackageSetPlan`.

The final path must exist and identify a regular file. A directory, FIFO,
socket, device, or other non-regular file is rejected. A symbolic link in the
final manifest-path component is rejected whether its target exists or is
broken. Parent components follow normal operating-system path resolution; v0.1
does not reject symlinked parent components and does not claim a complete
defense against concurrent filesystem races.

After the binary bounded read, BOM check, and strict UTF-8 decoding, the reader
delegates all JSON and configuration semantics to
`parse_class_world_manifest`. It does not duplicate the JSON schema, rebuild a
`PackageSetPlan`, load or validate packages, plan registrations, or apply a plan.

On success, `ClassWorldManifestFileReadResult.configuration` contains the
complete immutable configuration and `is_read` is true. Transport issues are in
`issues`. If transport succeeds but parsing fails, `issues` remains empty,
`configuration` is `None`, and `manifest_issues` contains the parser's exact
immutable issues in their existing order. Malformed JSON, duplicate keys,
unknown fields, and package-plan mismatches are therefore not hidden behind a
generic read error.

## Write contract and replacement policy

`write_class_world_manifest_file(configuration, path)` first delegates to
`serialize_class_world_manifest`, then strictly encodes and size-checks the
canonical text. It does not parse after writing or read the destination back.

The destination parent must already exist and be a directory. The writer never
creates parent directories or searches another location. The final destination
may be absent or an existing regular file. An existing directory, non-regular
file, or final-component symlink is rejected.

Writing is an explicit atomic replacement operation:

- an absent destination is created;
- an existing regular destination is atomically replaced;
- existing contents are not merged;
- no backup is generated; and
- every filesystem metadata attribute is not guaranteed to be preserved.

The caller owns destination selection.

## Atomic-write flow

The writer:

1. creates a recognizably private temporary file in the destination directory
   with `tempfile.mkstemp`, which uses exclusive creation semantics;
2. writes every canonical UTF-8 byte;
3. flushes the temporary stream;
4. calls `os.fsync` on the temporary file descriptor;
5. closes the temporary file; and
6. calls `os.replace(temporary_path, destination_path)`.

The temporary filename differs from the destination, contains no student or
manifest content, and is never included in public diagnostics. Same-directory
placement keeps replacement on the destination filesystem.

No partial new content is written through the destination pathname before
replacement. Serialization, encoding, size, parent, destination, temporary-file
creation, write, flush, file-sync, and replacement failures return zero
`bytes_written`. A failure before replacement leaves the prior destination
unchanged. After a temporary file exists, failure triggers best-effort cleanup.
If cleanup also fails, the original issue remains first and a separate
`TEMP_FILE_CLEANUP_FAILED` issue follows; the result does not claim complete
cleanup.

On success, `ClassWorldManifestFileWriteResult.bytes_written` is the exact UTF-8
byte count, `issues` is empty, and `is_written` is true.

## Concurrency, crashes, and durability

v0.1 provides atomic replacement visibility, not a multi-process transaction or
database-grade durability:

- no file lock coordinates threads or processes;
- callers must coordinate concurrent writers;
- the last completed replacement may become visible;
- a process crash before replacement should leave the old destination intact
  but may leave a private temporary file;
- a crash after replacement may leave the new destination visible;
- stale temporary cleanup after a process crash is not implemented; and
- the directory entry is not synchronized, so no power-loss durability claim is
  made for the replacement.

The initial final-path checks and later open or replacement are separate
filesystem operations. A concurrently changed path can therefore race those
checks. This policy is conservative about the observed final component but is
not a complete filesystem security boundary.

## Safety boundary

Manifest file transport performs no:

- YAML parsing or format negotiation;
- hashing, checksums, signing, or integrity metadata;
- release-manifest or release-artifact generation;
- package validation, loading, selection, planning, or application;
- class-world assembly or runtime target mutation;
- `World`, `Character`, or `Object` construction;
- student-code execution or asset materialization;
- Pygame, renderer, scene, lifecycle, or event-loop initialization;
- publication, approval, authentication, authorization, or registry mutation;
- network, cloud, database, or online-storage access;
- directory watching or automatic reload; or
- file locking, archives, deployment, or persistent transaction recovery.

## Deferred work

Deferred work includes:

- stale-temporary-file cleanup after process crashes;
- portable directory `fsync` durability;
- file locking and explicit concurrent-writer coordination;
- optional verified readback;
- release-declaration file transport;
- deterministic artifact hashing and signing;
- class-world assembly and asset materialization;
- publication, approval, authentication, registries, and online storage;
- release packaging and deployment; and
- persistent audit and recovery records.
