# Phase E Exact Approved-Version Class-World Pinning v0.1

> **Status:** Implemented bounded application-service and reference-persistence
> adapter. Owner authority is recorded in
> [GitHub issue #31](https://github.com/tonyluo2000/explore-studio/issues/31).
> This slice adds no endpoint and does not alter Class-World construction,
> assembly, or release semantics.

## Boundary

`ClassWorldPinningService` binds one exact package pin already present in an
`AuthoritativeClassWorldConfiguration` returned by the server-side
[configuration loader](phase-e-configuration-store-v0.1.md) to one currently
approved registry entry. It rejects raw or caller-constructed configuration
objects. It does not create, edit, rebuild, serialize to disk, or release that
configuration.

The request contains only exact `package_id`, exact Semantic Version,
correlation ID, and idempotency key. `latest`, ranges, prefix matching,
fallback, listing, and replacement are unsupported. Owner, cohort, digest,
compatibility, artifact reference, approval state, and approval identity are
never accepted as request claims.

Before authorization, the adapter requires the loaded record to match immutable
state in the same store, invokes the existing canonical configuration serializer
as a defensive validation boundary, and compares its SHA-256 with the stored
server-derived digest. The requested package ID/version must already be one of
the configuration's exact pins. No package-set or configuration build function
is called by pinning.

## Registry binding and authorization

Under one `BEGIN IMMEDIATE` transaction, the service:

1. re-resolves the verified OIDC issuer/subject through the immutable actor
   binding;
2. resolves only the exact package ID/version through the approved registry
   projection;
3. compares the configuration cohort and Student API compatibility with the
   projected authoritative values;
4. reloads current cohort membership and requires course-admin role and
   AAL2/MFA; and
5. calls the central deny-by-default `pin` policy with the current projected
   owner, cohort, package identity, digest, and approval state.

Teachers and students cannot use this configuration-pinning adapter even though
the foundation's more general policy model includes a teacher pin capability.
Missing, reviewable, rejected, revoked, cross-cohort, and unauthorized exact
versions all produce the same access-denied result.

## Immutable pin identity

A successful operation creates an opaque UUIDv4 pin record containing:

- Class-World ID/version and SHA-256 of the complete canonical configuration;
- exact package ID/version and raw archive SHA-256;
- authoritative cohort, current namespace owner, and Student API compatibility;
- immutable artifact/submission reference and approval decision identity;
- course-admin actor, role/AAL2 membership snapshot and revision;
- pin timestamp, correlation ID, and idempotency key.

The authoritative configuration create operation establishes the immutable
binding for the Class-World ID/version, canonical configuration digest, cohort,
and Student API version before pinning. Every package pin under that
configuration identity must reference the same binding. Only one pin may exist for a
`(class_world_id, class_world_version, package_id)` identity. Both binding and
pin rows reject update and delete. A matching duplicate returns the original
pin; a changed configuration digest, version, registry binding, approval
identity, or replay payload fails closed. Persistence independently rechecks
that a new row equals the current approved registry projection.

## Revocation, concurrency, and audit

Pin creation and review decisions use the same serialized write transaction.
A concurrent pin/revocation therefore commits in one coherent order: the pin
may complete before revocation, or it is denied after revocation. No pin can be
created from a post-revocation or stale registry entry.

Revocation prevents all future and replayed pin operations for that version. It
does not update or delete earlier pin records, configurations, submissions,
package versions, approval decisions, or release identities. Consumers of a
historical pin retain its exact provenance, while any later operation must
enforce current policy independently.

The append-only pin, audit event, and actor-scoped completed idempotency result
commit atomically. Audit details retain the exact configuration digest, package
digest, compatibility, artifact reference, and approval decision identity.
Identical concurrent or replayed requests converge to the original pin; replay
rechecks current course-admin authority and current approval first.

## Explicit exclusions

This slice adds no:

- Class-World configuration authoring or mutation;
- package-set planning, build, assembly, or release behavior;
- endpoint, list/search operation, or `latest` resolution;
- signing or attestations;
- deployment or release publication;
- moderation; or
- student-code execution or isolation.
