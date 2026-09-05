# Phase E Approved Registry Projection v0.1

> **Status:** Implemented bounded application-service and reference-persistence
> contract. Owner authority is recorded in
> [GitHub issue #31](https://github.com/tonyluo2000/explore-studio/issues/31).
> This slice adds no endpoint or Class-World pinning workflow.

## Projection

The registry is a derived, non-materialized projection over authoritative
immutable package submissions, package-version identities, namespaces, and
append-only review decisions. It has no mutable registry table and therefore no
separate version binding that can be replaced or drift from its source records.

An entry exists only when the latest decision for an exact submission is the
allowed `reviewable -> approved` transition. Reviewable, rejected, and revoked
submissions do not project. The sole lookup accepts an exact package ID and
Semantic Version; `latest`, version ranges, prefix matching, fallback, listing,
and search are not supported.

Every projected entry contains:

- the current authoritative namespace owner and cohort scope;
- exact package ID, semantic version, and server-derived raw ZIP SHA-256;
- validated Student API compatibility from immutable submission provenance;
- the opaque submission UUID as the immutable artifact reference; and
- the approving decision UUID and timestamp.

The lookup accepts none of those values other than package ID and exact version
from the caller. It never reads identity, owner, cohort, digest, compatibility,
artifact reference, approval state, or approval identity from client claims.

## Authorization and BOLA handling

`ApprovedRegistryService` resolves a verified OIDC issuer/subject through the
existing immutable actor binding. Under one `BEGIN IMMEDIATE` transaction it
derives the current entry, reloads current cohort membership, and calls the
central deny-by-default `registry-read` policy with server-derived resource
attributes.

Current active membership is mandatory. Students may read a currently approved
entry in their cohort; teachers and course-admins require current same-cohort
membership and AAL2/MFA. Missing, unapproved, revoked, rejected, and
cross-cohort exact versions all return the same unavailable result, so object
identifiers do not act as authorization secrets or existence oracles.

## Coherence, revocation, and audit

Approval, revocation, and audited registry reads all acquire the same serialized
SQLite write transaction. A read therefore observes either the complete state
before a concurrent transition or the complete state after it, never a split
projection. A successful read does not confer future pin eligibility; a later
pin operation must recheck current approval and authorization.

Revocation appends `approved -> revoked`. The next projection lookup returns no
entry, including an idempotent replay of a formerly successful read. Historical
submission, package-version, artifact, approval, revocation, and prior read
audit records remain unchanged.

Each successful logical read appends an audit event containing the exact package
identity and digest, cohort scope, owner, compatibility, artifact reference,
approval decision identity, and correlation ID. The event and actor-scoped
completed idempotency record commit atomically. Identical concurrent/replayed
lookups converge to one audit record while current projection and authority are
rechecked; a changed lookup under the same key fails closed.

## Explicit exclusions

This slice adds no:

- HTTP endpoint, list/search API, or `latest` resolution;
- Class-World configuration or package pinning;
- signing or attestations;
- deployment or release publication;
- moderation; or
- student-code execution or isolation.
