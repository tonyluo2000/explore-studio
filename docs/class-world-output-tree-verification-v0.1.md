# Class-World Materialized Output-Tree Verification v0.1

> **Status:** Implemented descriptor-confined readback of the materialized
> output tree and per-artifact SHA-256 and byte-count verification against one
> already successfully verified assembled-output manifest. Archive parsing or
> extraction, package loading, student-code execution, signing, approval,
> authentication, publication, and deployment remain outside this contract.

This contract answers one narrow question:

> Do the files under this explicitly supplied output root match — exactly, by
> relative path, byte count, and SHA-256 — the package set recorded in this
> successfully verified assembled-output manifest?

```text
verified ClassWorldAssembledOutputManifestFileDigestVerificationResult
        +
explicit output root
        ↓
consume only the retained canonical manifest projection (no manifest reparse)
        ↓
validate every manifest-authorized relative path fail-closed
        ↓
normalized-collision preflight over the authorized path set
        ↓
descriptor-relative O_DIRECTORY | O_NOFOLLOW traversal from the output root
        ↓
bounded read-only read; enforce manifest byte counts and existing read limits
        ↓
recompute SHA-256 and compare to the manifest digest fields
        ↓
verify the aggregate byte total
        ↓
immutable ClassWorldOutputTreeVerificationResult
```

## Public API

```python
from explore.packages import verify_class_world_output_tree

result = verify_class_world_output_tree(verified_manifest_result, "/absolute/output-root")
if result.is_verified:
    for artifact in result.artifacts:
        assert artifact.digest_algorithm == "sha256"
```

The public contract includes:

- `verify_class_world_output_tree`;
- `ClassWorldVerifiedOutputArtifact`;
- `ClassWorldOutputTreeVerificationResult`;
- `ClassWorldOutputTreeVerificationIssue` and its stable issue-code enum; and
- `SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION`.

The contract version is `"0.1"`.

## Inputs and validation order

The operation accepts only:

1. one `ClassWorldAssembledOutputManifestFileDigestVerificationResult` whose
   `is_verified` property is `True`; and
2. one explicit non-empty absolute `str` or `pathlib.Path` output root.

Validation order is:

1. verified manifest-file result type and `is_verified`;
2. retained canonical manifest self-consistency — supported contract version,
   non-empty canonical package tuple, non-negative byte counts, and a
   `total_bytes` equal to the sum of package byte counts;
3. output-root value, existence, regular-directory type, and a resolved path
   with no symbolic-link component;
4. per-package `digest_algorithm` / `digest_hex` and canonical relative-path
   validation;
5. a normalized (`NFC` + case-fold) collision preflight over the authorized
   relative-path set;
6. platform descriptor-confinement availability; and
7. descriptor-confined per-artifact read, byte-count, digest, and aggregate
   checks in canonical manifest order.

Manifest and output-root value failures perform no filesystem reads beyond
inspecting the output root itself. The manifest file is never reopened or
reparsed: this layer consumes only the manifest projection already retained on
the successfully verified result, and it never rebuilds or re-serializes that
projection.

## Descriptor-confined, root-confined reads

Only paths listed in the manifest are inspected. For each authorized package,
in canonical order:

- every path component is `lstat`-checked for a symbolic link;
- the lexically resolved candidate must remain inside the resolved output root;
- traversal opens the output root and every intermediate directory with
  descriptor-relative `O_DIRECTORY | O_NOFOLLOW`, and opens the final artifact
  with `O_RDONLY | O_NOFOLLOW`;
- the opened descriptor must be a regular file; and
- a `(st_dev, st_ino)` identity already seen for another package fails closed as
  an alias or collision.

Descriptor-confined traversal is mandatory; platforms without `dir_fd`,
`O_DIRECTORY`, or `O_NOFOLLOW` support fail closed. Symbolic links, path escape,
normalized-path aliases, hard-link aliases, and non-regular components therefore
all fail closed with no verified result.

## Byte counts, digests, and aggregate total

Each artifact is read read-only. The reader:

- rejects a manifest `bytes_written` above the existing 64 MiB per-artifact
  limit, and a running total above the existing 256 MiB aggregate limit;
- requires the on-disk size to equal the manifest `bytes_written`, and requires
  the bounded read (`bytes_written + 1` requested) to return exactly that many
  bytes; and
- recomputes lowercase hexadecimal SHA-256 over the bytes and requires equality
  with the manifest `digest_hex`.

After every package is verified, the sum of verified byte counts must equal the
manifest `total_bytes`.

## Result and trust boundary

A successful `ClassWorldOutputTreeVerificationResult` retains the exact manifest
object, one `ClassWorldVerifiedOutputArtifact` per package in canonical manifest
order, and the verified aggregate `total_bytes`. Any failure returns no
artifacts, no total, and one deterministic issue.

Successful verification proves only that the files at the manifest-authorized
relative paths under the supplied output root currently match the manifest's
recorded identities, paths, byte counts, and digests. It does not prove
authenticity, approval, publication status, archive safety, or package
semantics, and it inherits — without expanding — the upstream manifest trust
boundary.

This tranche performs no output-tree mutation, directory enumeration, detection
of unlisted files, manifest reparse or recomposition, archive parsing or
extraction, package loading, student-code execution, runtime registration,
network, signing, approval, authentication, publication, or deployment work.
