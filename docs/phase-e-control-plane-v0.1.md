# Phase E Authenticated Control Plane v0.1

> **Status:** Implemented domain-service and reference-persistence contract.
> Owner authority is recorded in
> [GitHub issue #31](https://github.com/tonyluo2000/explore-studio/issues/31).
> This slice deliberately adds no HTTP, OIDC, session, or CSRF endpoint.

## Boundary

`ControlPlaneService` implements only these authenticated administrative
transitions:

- create, change, or revoke one cohort membership;
- claim one globally unique package namespace;
- create, reactivate, or revoke one explicit same-cohort `submit` grant; and
- transfer current namespace ownership to another active member of the same
  cohort.

Every request contains target intent and exact expected revisions. It contains
no trusted current role, authority assurance, grantor, current owner, current
cohort scope, or current state. No request can create or rebind a federated
actor identity.

## Authentication and authorization

The service accepts only an `AuthenticatedOIDCIdentity` produced by a future
trusted OIDC adapter. It resolves the configured issuer and opaque subject to
the existing immutable actor binding. Under the serialized write transaction,
it reloads current membership and uses the central deny-by-default
control-plane action matrix as the administrative authority gate.

Every transition requires an active same-cohort course-admin membership and
AAL2/MFA. Student, teacher, AAL1, inactive, unbound, cross-cohort, and unknown
object cases fail closed. Unknown and cross-cohort namespace identifiers use
the same access-denied result. A course-admin cannot change or revoke the
membership supplying their own in-flight authority snapshot; another current
course-admin must perform that transition.

## Optimistic state transitions

Membership identity remains `(cohort_id, actor_id)`. Creation requires expected
revision zero and creates revision one. A role change or revocation must match
the exact current active revision and increments it once. Revocation sets the
current membership inactive; it does not delete actor or membership identity.

Namespace identity remains the global `package_id` plus its immutable cohort
and creation time. A claim requires expected revision zero. Transfer compares
the exact current namespace revision, changes only current owner metadata, and
increments the revision once. It never changes existing package IDs, versions,
bytes, digests, submitting actors, approvals, registry history, or pins.

Explicit submit grants have a separate persistent active/revision state. The
first grant requires expected revision zero, revocation increments its revision
and removes only the effective grant, and an explicit later regrant increments
the same state identity again. Grant/revoke also compares the namespace
revision so a stale request cannot cross a concurrent ownership transfer.

## Replay, audit, and persistence

Every successful operation appends an immutable UUIDv4 control-plane
transition containing:

- the exact action, cohort, target type, and target identity;
- canonical before/after state and revisions;
- the authorizing actor's current course-admin role, AAL2 assurance,
  membership grantor/time/revision, and active status; and
- transition time, correlation ID, and actor-scoped idempotency key.

The corresponding append-only audit event repeats the authoritative membership
snapshot and canonical change document. Its retention deadline is cohort close
plus two years, or transition time plus two years when later. The current-state
mutation, transition, audit event, and completed idempotency result commit in
one `BEGIN IMMEDIATE` transaction.

An identical retry returns the original immutable transition only after current
same-cohort AAL2 course-admin authority is rechecked. Reusing the key with a
changed request fails closed. Competing identical operations converge; stale
or conflicting operations commit at most one exact next revision.

`SQLiteControlPlaneStore` is the full additive Phase E reference store. A
production database must preserve all foreign keys, immutable identities,
append-only ledgers, optimistic comparisons, and transaction boundaries.

## Preserved boundaries

This slice does not add or change:

- HTTP routes, OIDC exchange, sessions, cookies, or CSRF behavior;
- submission, archive verification, review, registry, or pinning semantics;
- local development, validation, loading, export, or Class-World construction;
- signing, attestations, deployment, moderation, or publication infrastructure;
  or
- student-code execution or isolation.
