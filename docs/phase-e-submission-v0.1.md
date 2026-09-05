# Phase E Package Submission v0.1

> **Status:** Implemented bounded application-service and reference-persistence
> contract. Owner authority is recorded in
> [GitHub issue #31](https://github.com/tonyluo2000/explore-studio/issues/31).
> This slice deliberately adds no HTTP endpoint or approval workflow.

## Boundary

This contract implements only authenticated publication of one deterministic
Explorer Package export into an immutable, reviewable submission:

```text
commit ≠ export ≠ submit/publish ≠ approve ≠ release
```

`PackageSubmissionService` accepts exactly one filename and one bytes value. It
does not accept package owner, cohort, role, package ID, semantic version, raw
digest, approval state, or release state from the caller. The trusted OIDC
adapter supplies a verified issuer, subject, and assurance level; the service
resolves that pair through the existing immutable federated binding and never
creates an actor during submission.

Each publication includes an explicit acknowledgment matching the service's
current trusted terms and license-policy versions. The record captures the
represented authority, internal actor, immutable package version, and time.

## Authorization

The service derives `package_id` from the validated manifest, loads the global
namespace and cohort from persistence, reloads current membership and explicit
grants, and calls the central deny-by-default `submit` policy. A student must be
an active member of the namespace's cohort and must own the namespace or hold
an explicit same-cohort `submit` grant. A cohort at or after its close time is
inactive for new submissions. Missing and forbidden namespace IDs produce the
same denial.

Authorization is repeated under a `BEGIN IMMEDIATE` write transaction. An
idempotent replay also rechecks current authorization under that lock, so a
completed operation key cannot restore revoked membership or grant authority.

## Archive verification

The filename must be exactly
`{package-id}-{semantic-version}.explorer-package.zip`. The raw archive is
bounded by the existing deterministic-export limits. Ingest then:

1. computes raw ZIP SHA-256 server-side;
2. safely parses a bounded UTF-8 `manifest.yaml` with no YAML aliases, anchors,
   custom tags, excessive tokens, or excessive nesting;
3. requires members to be exactly `manifest.yaml`, declared contributions in
   manifest order, and declared assets in manifest order;
4. bounds member count, individual bytes, aggregate bytes, manifest bytes, and
   declarative YAML bytes;
5. reconstructs the canonical ZIP and requires byte-for-byte equality with the
   deterministic export v0.1 contract; and
6. runs existing Explorer Package v0.1 validation and declarative loading in a
   confined temporary directory.

Only safe YAML and explicitly declared media bytes are inspected. No Python is
imported or executed, no dependency is installed, and no package command runs.

## Identity, submission, and persistence

The immutable package identity is:

```text
(package_id, semantic_version) -> exactly one raw_archive_sha256
```

Conflicting bytes for an existing exact version fail closed. A successful
publication creates a server-generated opaque UUIDv4 `submission_id`. The only
created lifecycle state is `reviewable`; it does not mean approved, registered,
pinned, configured, or released.

The package-version row, original ZIP bytes, validation outcome and per-member
digest provenance, publication acknowledgment, append-only audit event, and
completed idempotency result commit atomically. Submission rows and artifact
bytes reject update and delete. Artifact retention is cohort close plus one
calendar year; the audit event retention deadline is cohort close plus two
calendar years.

An identical actor-scoped retry with the same operation key and request returns
the original `submission_id`. Reusing the key with different filename, bytes,
or acknowledgment fails closed. Competing identical writers serialize and
produce one package version, one submission, one audit event, and one result.

## Explicit exclusions

This slice does not add:

- OIDC protocol exchange, login, sessions, recovery, or HTTP endpoints;
- teacher review decisions, approval, rejection, or revocation transitions;
- an approved registry projection or list/search service;
- Class-World pinning or configuration mutation;
- signing or attestations;
- deployment or publication infrastructure;
- moderation; or
- student-code execution or isolation.
