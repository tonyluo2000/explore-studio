# Phase E Synthetic Staff Pilot Hardening v0.1

> **Status:** Implemented pilot composition around the merged staff transport.
> This authorizes only staff accounts and pre-seeded synthetic/non-minor data.

## Configuration and secrets

`StaffPilotConfig` is the complete non-secret configuration model. It fixes the
public HTTPS origin, TLS termination mode, narrow trusted-proxy CIDRs, one
absolute SQLite path, one synthetic environment identity, exactly one worker,
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

The cumulative Phase E migrations run before the pilot marker is inserted.
HTTP operations, cleanup, and emergency revocation share one re-entrant lock,
preserving the existing reference-store transaction guarantees. A later
multi-worker/database adapter must re-establish the same atomicity before the
single-worker constraint can be removed.

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
database quick check, current AAL2 approval of every configured issuer, and
cleanup freshness. Neither endpoint emits provider, path, actor, object, or
datastore details.

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
