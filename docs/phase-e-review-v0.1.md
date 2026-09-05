# Phase E Package Review Decisions v0.1

> **Status:** Implemented bounded application-service and reference-persistence
> contract. Owner authority is recorded in
> [GitHub issue #31](https://github.com/tonyluo2000/explore-studio/issues/31).
> This slice deliberately adds no endpoint, registry projection, or release
> workflow.

## State machine

Every immutable submission begins `reviewable`. Its current review state is
derived from an append-only decision log with exactly these transitions:

```text
reviewable -> approved
reviewable -> rejected
approved   -> revoked
```

No other transition exists. Rejected and revoked versions are terminal; a
correction must be submitted under a new semantic version. Decisions never
rewrite the submission, its package-version identity, validation provenance,
or raw archive bytes.

## Authorization

`PackageReviewService` accepts a verified OIDC identity, opaque `submission_id`,
and bounded decision intent. It accepts no client claims for actor, role,
cohort, package/version/digest, owner, submitter, or current state.

The service resolves the immutable issuer/subject binding and reloads the
submission, namespace, exact package identity, cohort membership, and current
review state under a `BEGIN IMMEDIATE` transaction. The central deny-by-default
policy requires AAL2/MFA and an active same-cohort teacher or course-admin role
for approval or rejection. The package owner and submitter cannot approve or
reject their own submission. Revocation is restricted to a same-cohort
course-admin.

Missing and unauthorized submission identifiers return the same access-denied
result. Idempotent replay rechecks current authorization before returning the
original decision.

## Immutable decisions and atomicity

Each successful transition appends a UUIDv4 decision containing:

- exact submission and package-version identity;
- transition sequence, action, prior state, and resulting state;
- authoritative reviewer actor plus cohort, role, AAL2 assurance, membership
  grantor/time/revision/active snapshot;
- bounded reason and canonical bounded result metadata;
- decision timestamp, correlation ID, and actor-scoped idempotency key.

The schema rejects updates and deletes. It constrains each row to an allowed
transition and the store checks that its prior state and sequence extend the
current log. SQLite write serialization makes competing decisions observe one
coherent current state. Identical retries converge on the original decision;
changed requests under the same key and incompatible concurrent transitions
fail closed.

Decision persistence, append-only audit, and the completed idempotency record
commit in one transaction. Audit records identify the decision and transition,
retain the exact package digest and membership revision, and hash bounded reason
and result metadata rather than duplicating their contents.

## Revocation semantics

Revocation is prospective only. It appends `approved -> revoked` and does not
delete or mutate the approved decision, package bytes, submission, package
identity, historical configuration, or release identity. This slice neither
finds nor rewrites consumers of an earlier approval.

## Explicit exclusions

This slice adds no:

- OIDC protocol exchange, login/session, or HTTP endpoint;
- approved-registry projection or list/search service;
- Class-World pinning or configuration mutation;
- signing, attestations, deployment, or release publication;
- moderation; or
- student-code execution or isolation.
