# Phase E Authoritative Class-World Configuration Store v0.1

> **Status:** Implemented server-side immutable persistence and loading contract.
> Owner authority is recorded in
> [GitHub issue #31](https://github.com/tonyluo2000/explore-studio/issues/31).
> This slice deliberately adds no HTTP, OIDC, session, or configuration-authoring
> workflow.

## Boundary

This contract persists one configuration already produced by a trusted internal
Class-World workflow and later reconstructs it solely from immutable server
state. It does not accept a configuration document as request data and does not
create, edit, build, assemble, release, or deploy a Class-World.

`ConfigurationCreateRequest` contains only expected revision zero, correlation
ID, and idempotency key. `ConfigurationLoadRequest` contains only a
server-generated opaque UUIDv4 locator, correlation ID, and idempotency key.
Neither request can carry or override Class-World identity, version, digest,
cohort, compatibility, package pins, package-set plan, or content. There is no
latest, range, prefix, fallback, list, or rebinding operation.

## Immutable persistence

The trusted preparation boundary invokes the existing canonical Class-World
serializer. The service derives SHA-256 from its exact canonical UTF-8 bytes.
Under one serialized transaction, an authorized create binds and appends:

- the exact `(class_world_id, class_world_version)` identity;
- one opaque server-generated locator;
- the canonical bytes and their server-derived SHA-256;
- immutable cohort scope and Student API compatibility;
- the current course-admin AAL2 authority snapshot; and
- create audit and actor-scoped completed idempotency evidence.

Configuration and binding rows reject update and delete. Creation requires
expected revision zero. Identical retries converge; changed idempotency payloads
and any attempt to bind the exact identity to different bytes, cohort, or
compatibility fail closed.

## Authoritative loading

The loader resolves only the opaque exact locator. It authorizes a current
same-cohort course-admin at AAL2 before returning configuration state. Missing
and cross-cohort locators produce the same unavailable result.

For every successful load, it:

1. recomputes and compares the canonical-byte SHA-256;
2. reads every exact package pin from the stored canonical manifest;
3. loads the corresponding immutable server-side submission artifact;
4. verifies its stored SHA-256 and reruns bounded deterministic archive
   verification and declarative loading;
5. rebuilds the package-set plan through the existing preflight contract;
6. parses the stored manifest against that plan through the existing
   Class-World parser; and
7. reserializes the result and requires byte-for-byte equality plus exact
   identity, cohort, and compatibility equality.

Any digest mismatch, tamper, absent source, cross-cohort source, parse failure,
or canonical mismatch returns no authoritative object. No student code is
imported or executed.

## Pinning boundary and audit

Only the loader can issue the sealed `AuthoritativeClassWorldConfiguration`
consumed by `ClassWorldPinningService`. The pinning service rejects a raw
`ClassWorldConfiguration`, verifies the loaded record still matches the same
store, and requires the pre-existing immutable configuration binding. Pinning
cannot create or rebind configuration authority.

Successful logical creates and loads append audit events with the opaque
locator, exact identity, digest, cohort, compatibility, purpose, and correlation
ID. Audit plus completed idempotency evidence commit atomically with creation;
load audit and idempotency also commit in one serialized transaction. Replays
recheck current authority and reconstruction without duplicating audit.

## Explicit exclusions

This slice adds no:

- HTTP route, OIDC exchange, session, cookie, or CSRF behavior;
- configuration authoring, mutation, latest/range lookup, listing, or search;
- package upload or real-minor-data enablement;
- Class-World build, assembly, materialization, or release semantic change;
- signing, attestations, deployment, moderation; or
- student-code execution or isolation.
