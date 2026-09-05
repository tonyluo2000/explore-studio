# Phase E Synthetic Staff Pilot Hardening v0.1

> **Status:** Implemented pilot composition around the merged staff transport.
> This authorizes only staff accounts and pre-seeded synthetic/non-minor data.

## Configuration and secrets

`StaffPilotConfig` is the complete non-secret configuration model. It fixes the
public HTTPS origin, TLS termination mode, narrow trusted-proxy CIDRs, one
absolute SQLite path, one synthetic environment identity, one reviewed seed
attestation, exactly one worker,
session/OIDC bounds, maintenance cadence, JWKS freshness/outage grace, and each
approved OIDC issuer/client/AAL mapping. Every redirect URI must equal the
provider-specific callback at the public origin.

OIDC client credentials are represented only by `env:EXPLORE_STAFF_SECRET_*`
references. `SecretLoader` is the narrow adapter interface for a production
secret manager. `EnvironmentSecretLoader` is the pilot adapter for
process-injected secrets; loaded values use a non-printing wrapper. No example
credential, `.env` file, or secret-bearing configuration is committed.

## TLS and proxy trust

Direct mode requires an HTTPS ASGI scope and rejects forwarding headers.
Trusted-proxy mode accepts TLS metadata only when the immediate peer belongs to
an explicitly configured narrow CIDR and supplies one exact public forwarded
host plus `https` scheme. The wrapper strips all forwarding headers before the
application sees the request. Host and origin checks in the existing transport
remain in force. Responses add HSTS to the existing no-store, CSP, referrer,
framing, and content-type protections.

## Synthetic datastore and concurrency

The bootstrap accepts only an absolute `.sqlite3` target under an existing
non-symlink directory. It will not adopt a non-empty database unless it already
contains the immutable matching `synthetic-non-minor` environment marker. The
database and adjacent process lock are mode `0600`; a non-blocking filesystem
lock rejects a second process. Configuration also rejects any worker count
other than one.

The supported launch model is one non-reloading ASGI worker that constructs the
runtime inside that final worker process and enables ASGI lifespan. Preloaded or
preforked application runtimes, multiple workers, worker reloaders, and a
runtime constructed in a supervisor before forking are unsupported. The
datastore records its creating PID; lifespan startup and requests reject an
inherited runtime. An inherited child closes only its copy of the descriptors
and cannot explicitly unlock the parent's process lease.

The cumulative Phase E migrations run before the pilot marker is inserted.
HTTP operations, cleanup, and emergency revocation share one re-entrant lock,
preserving the existing reference-store transaction guarantees. A later
multi-worker/database adapter must re-establish the same atomicity before the
single-worker constraint can be removed.

## Synthetic seed attestation

`PilotSeedAttestation` names the reviewed synthetic seed provenance, version,
and SHA-256 digest. The runtime verifies the exact bounded immutable
`seed_artifact` bytes against that digest before datastore creation and passes
those same bytes to the one trusted startup `seed_initializer`. A new datastore
is structurally initialized but remains unready until that initializer
completes. The initializer is an internal bootstrap callback, never an HTTP or
product ingestion surface. The runtime verifies that every configured staff
issuer is approved at AAL2 and that no OIDC transaction or staff session exists
before it inserts the immutable attestation.

Missing or mismatched attestation fails readiness; an existing mismatched
attestation is refused at bootstrap, and an attested datastore cannot be
reseeded. A failed or interrupted initializer leaves the datastore unattested
and requires the synthetic reset procedure; it is never resumed in place. The
attestation identifies a reviewed seed artifact and does not make
arbitrary data synthetic: operators must independently verify its provenance
and review the initializer that interprets it. Pilot datastore schema v1 is not
adopted by v2 and must follow the synthetic reset procedure.

## OIDC availability and maintenance

JWKS documents are cached for a bounded fresh interval. An unknown or ambiguous
key identifier forces one refresh, supporting normal rotation. Fetch failures
may use the last document only for the configured short outage grace; after
that the login fails closed. Token exchange is never cached. Bearer token type
comparison is standards-compatible and case-insensitive.

The application lifespan runs cleanup at startup and periodically thereafter.
Cleanup removes expired one-time OIDC transactions and inactive session
material. Internal maintenance hooks revoke all sessions for one actor or one
issuer. Readiness fails if cleanup becomes stale.

## Health and observability

`GET /health/live` reports only `{"status":"ok"}`. `GET /health/ready` reports
only `ready` or `unavailable`, based on the immutable synthetic marker, schema,
immutable seed attestation, database quick check, current AAL2 approval of every
configured issuer, and cleanup freshness. Datastore, provider, topology, and
trusted-clock exceptions are owned by the health boundary and become the same
secured, non-cacheable `503` response plus bounded readiness-failure telemetry.
Neither endpoint emits provider, path, actor, object, datastore, exception, or
traceback details.

Operational logs contain method, route template, status class, bounded elapsed
time, and an optional one-way correlation tag. Metrics expose the same bounded
aggregate labels internally. Request paths, query strings, bodies, cookies,
tokens, subjects, locators, package identifiers, and secrets are never logged.

## Boundary

The inner routes and Phase E authorization services are unchanged. The pilot
adds no student onboarding, submission/upload, review UI or route, registry
listing/search, configuration authoring, real-minor data, signing, moderation,
deployment automation, or student-code execution.

Operational procedures:

- [incident response](operations/staff-pilot-incident.md);
- [rollback](operations/staff-pilot-rollback.md);
- [OIDC secret rotation](operations/staff-pilot-secret-rotation.md); and
- [synthetic data reset](operations/staff-pilot-synthetic-reset.md).
