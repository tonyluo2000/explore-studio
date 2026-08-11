# Class-World Release Declaration File Transport v0.1

> **Status:** Implemented explicit bounded local UTF-8 file transport for
> release-declaration JSON. Deterministic release-declaration serialization and
> strict parsing are separate layers. Deterministic digesting is implemented
> separately, as is pure in-memory digest verification. Verified declaration-
> file readback is implemented as a separate composition layer. Raw file-byte
> hashing, artifact hashing, inventories, class-world assembly, signing,
> publication, and deployment remain deferred.

Class-World Release Declaration File Transport v0.1 moves deterministic
release-declaration JSON across one explicit local filesystem boundary:

```text
immutable ClassWorldReleaseDeclaration
        ↓
existing canonical serializer
        ↓
strict UTF-8 bytes without BOM
        ↓
same-directory atomic replacement

explicit local path
        ↓
bounded binary read and strict UTF-8 decoding
        +
authoritative immutable ClassWorldConfiguration
        ↓
existing strict release-declaration parser and builder
        ↓
immutable ClassWorldReleaseDeclaration
```

The recommended filename is:

```text
class-world.release.json
```

This is a convention only. Both APIs require the caller to supply an explicit
`str` or `pathlib.Path`. They do not infer a path or filename from release or
class-world identity, the current directory, repository state, the user home,
environment variables, or global settings.

## Architecture position

The architecture layers remain distinct:

1. `ClassWorldConfiguration` is the authoritative immutable configuration.
2. Class-world manifest JSON deterministically serializes configuration.
3. Manifest file transport moves manifest JSON at explicit local paths.
4. `ClassWorldReleaseDeclaration` records release identity and declared
   provenance derived from the authoritative configuration.
5. Release-declaration JSON provides deterministic serialization and strict
   parsing against that exact configuration.
6. Release-declaration file transport, implemented here, moves that JSON at an
   explicit local path.
7. [Release-declaration digesting](class-world-release-declaration-digest-v0.1.md)
   identifies canonical in-memory serialized declaration bytes without a file
   read.
8. [Release-declaration digest verification](class-world-release-declaration-digest-verification-v0.1.md)
   validates an expected digest and compares it with a recomputed in-memory
   declaration digest.
9. [Release-declaration file digest verification](class-world-release-declaration-file-digest-verification-v0.1.md)
   composes this reader with step 8 and verifies the canonical declaration
   represented by a file without hashing its raw bytes.
10. Future artifact layers may inventory, assemble,
   archive, sign, approve, publish, or deploy release content.

A release-declaration file is metadata, not a release artifact. This layer does
not assemble files or assets and does not prove that any release content exists
or matches the declaration.

## Contract constants

`SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION` is
exactly `"0.1"`. It versions filesystem transport semantics and is distinct
from `SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION`, which versions the
in-memory declaration and JSON schema.

`MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES` is exactly 1 MiB:

```python
1 * 1024 * 1024
```

The limit is measured in encoded UTF-8 bytes, never Unicode code points.
Release declarations are metadata, so this limit is intentionally
conservative.

## Public read API

```python
from explore.packages import read_class_world_release_declaration_file

result = read_class_world_release_declaration_file(
    path,
    configuration,
)

if result.is_read:
    assert result.declaration is not None
    declaration = result.declaration
else:
    for issue in result.issues:
        print(issue.code, issue.location, issue.message)
```

The reader:

1. validates the explicit path type and value;
2. rejects a final-component symbolic link;
3. requires an existing regular file;
4. performs one bounded binary read of at most
   `MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES + 1` bytes;
5. rejects an observed byte beyond the limit before decoding or parsing;
6. rejects a UTF-8 byte-order mark;
7. decodes with strict UTF-8;
8. delegates the complete text and authoritative configuration to
   `parse_class_world_release_declaration`; and
9. returns its declaration, serialization issues, and builder declaration
   issues without translating them.

The parser retains the exact supplied configuration instance on success:

```python
assert result.declaration is not None
assert result.declaration.configuration is configuration
```

The reader never reconstructs configuration, parses an embedded manifest,
rebuilds a `PackageSetPlan`, infers packages, or duplicates JSON validation.

## Public write API

```python
from explore.packages import write_class_world_release_declaration_file

result = write_class_world_release_declaration_file(
    declaration,
    path,
)

if not result.is_written:
    for issue in result.issues:
        print(issue.code, issue.location, issue.message)
```

The writer performs this sequence:

1. calls `serialize_class_world_release_declaration`;
2. encodes its exact text as strict UTF-8;
3. enforces the 1 MiB byte limit;
4. requires an existing directory parent;
5. permits a missing destination or an existing regular file;
6. rejects a final-component symbolic link or other existing file type;
7. creates one exclusive private temporary file in the destination directory;
8. loops until every byte has been written and rejects zero progress;
9. flushes the stream;
10. calls file `fsync`;
11. closes the stream; and
12. calls `os.replace` to atomically expose the completed file.

Successful bytes are exactly:

```python
serialize_class_world_release_declaration(declaration).encode("utf-8")
```

There is no BOM, newline conversion, appended data, or extra byte.
`bytes_written` counts committed destination bytes only. Bytes written to a
temporary file return as zero when replacement does not succeed.

A wrong programmer-level declaration type preserves the serializer's
`TypeError`. A manually inconsistent declaration produces the structured
`DECLARATION_INVALID` transport issue without creating a temporary file or
changing the destination.

## Path and file-type policy

Paths accept only `str` and `pathlib.Path`. `None`, bytes, integers, Booleans,
unrelated objects, empty strings, and whitespace-only strings are rejected.
Accepted values are not stripped or normalized.

The writer does not create parent directories or search fallback locations.
The destination parent must already exist and be a directory.

For reads, the final path must exist and be a regular file. Directories, FIFOs,
sockets, devices, final-component symlinks, and broken symlinks are rejected.
For writes, the destination may be absent or an existing regular file; all
other existing final-component types are rejected.

The final component is checked with `lstat` and is never intentionally followed
when it is a symlink. Parent-component symlinks follow ordinary operating-system
resolution, matching manifest transport v0.1. Preflight checks can race with
later operations, so this contract does not claim race-proof filesystem
security.

## UTF-8 and bounded reads

Files use UTF-8 without BOM. The reader rejects invalid UTF-8, truncated
multibyte sequences, UTF-16, UTF-32, a BOM followed by JSON, and a BOM-only
file. It never strips a BOM and never uses replacement decoding.

The reader requests at most the limit plus one byte. If the extra byte is
observed, it returns `FILE_TOO_LARGE` without decoding or invoking the parser.
This bounds memory used for file content even when the underlying file is much
larger.

## Atomic replacement and failure preservation

The exclusive temporary file resides in the destination directory, keeping
the final replacement on the same filesystem. A successful `os.replace`
atomically changes what readers opening the destination observe. Existing
regular files are replaced; writes never append, merge, back up, or create
versioned copies.

Before successful replacement, the old destination remains unchanged. If the
destination was absent, it remains absent. This holds for serialization,
encoding, size, parent inspection, destination inspection, temporary-file
creation, write, zero-progress write, flush, file `fsync`, close, and replace
failures.

After a temporary file exists, every ordinary failure attempts cleanup. If the
original operation and cleanup both fail, the original issue appears first and
`TEMP_FILE_CLEANUP_FAILED` appears second. Diagnostics never expose the
temporary filename. `KeyboardInterrupt` and `SystemExit` are not swallowed.

## Read results and issue separation

`ClassWorldReleaseDeclarationFileReadResult` is a frozen dataclass containing:

- `declaration`;
- transport `issues`;
- release-declaration `serialization_issues`; and
- release builder `declaration_issues`.

The result is all-or-nothing:

```text
transport failure: declaration=None, issues non-empty, parser tuples empty
parser failure:    declaration=None, serialization_issues non-empty
builder failure:   declaration=None, declaration_issues non-empty
success:           declaration non-None, every issue tuple empty
```

Duplicate-key, schema, exact-type, package-order, and configuration-agreement
issues remain serialization issues. Invalid release identity remains a builder
declaration issue. No partial declaration is returned.

`ClassWorldReleaseDeclarationFileWriteResult` is a frozen dataclass containing
committed `bytes_written` and an immutable tuple of transport issues.
`ClassWorldReleaseDeclarationFileIssue` is also frozen and contains a stable
code, privacy-safe message, and structural location such as `path`, `parent`,
`declaration`, `temporary_file`, or `destination`.

## Separate verification readback

After `os.replace`, the writer does not reopen, parse, compare, or hash the
destination. The separate
[Deterministic Class-World Release Declaration Digest v0.1](class-world-release-declaration-digest-v0.1.md)
hashes the in-memory serializer output, not a destination file. The
[Class-World Release Declaration Digest Verification v0.1](class-world-release-declaration-digest-verification-v0.1.md)
compares expected and recomputed in-memory digests; it also does not read the
destination. The separate
[Class-World Release Declaration File Digest Verification v0.1](class-world-release-declaration-file-digest-verification-v0.1.md)
now composes this reader with that verifier. The writer remains unchanged and
does not automatically read back or verify its output.

## Concurrency, crashes, and durability

There is no file locking or concurrent-writer coordination. Callers must
coordinate writes; the last completed atomic replacement may win. Destination
preflight and replacement can race with other filesystem actors.

The temporary file is flushed and file-`fsync`ed before replacement. Directory
`fsync` is not performed, so this contract makes no portable power-loss
durability guarantee for the directory entry. A process or machine crash can
leave a stale private temporary file, and v0.1 has no stale-temp discovery or
recovery. This is not a database transaction and provides no rollback after a
successful replacement.

## Safety boundary

Release-declaration file transport performs no:

- hashing, checksum, content fingerprint, or integrity verification;
- signing, key management, or attestation;
- artifact, package, or asset inventory;
- class-world assembly, asset copying, or output-directory generation;
- archive creation;
- package validation, loading, planning, or application;
- runtime world construction, Student API mutation, or Pygame work;
- network, HTTP, database, registry, or cloud-storage access;
- authentication, authorization, approval, or publication;
- deployment; or
- persistent audit-record creation.

## Deferred work

Deferred work includes:

- raw release-file byte digests, if separately required;
- assembled-artifact hashing and integrity verification;
- artifact, package, and asset inventories;
- class-world assembly and asset materialization;
- archive generation;
- signing, key management, and attestations;
- approval and publication;
- authentication, authorization, registries, and online storage;
- deployment;
- stale-temporary-file recovery and coordinated locking; and
- persistent audit and recovery records.
