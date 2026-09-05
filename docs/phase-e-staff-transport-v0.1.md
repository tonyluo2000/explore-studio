# Phase E Staff Transport Foundation v0.1

> **Status:** Implemented staff-only ASGI, OIDC, session, CSRF, and exact-object
> transport contract. Authority is [GitHub issue #31](https://github.com/tonyluo2000/explore-studio/issues/31)
> plus merged Phase E PRs #32–#38. This is an application boundary, not a
> deployment or real-minor-data launch approval.

## OIDC and identity

`StaffOIDCProvider` is server-owned configuration. Issuer, authorization,
token, JWKS, client, redirect, signing algorithm, and AAL mappings are never
selected or overridden by callback data. The flow uses authorization code plus
PKCE S256 and one-time, server-side transactions bound to independent state,
nonce, and secure browser-cookie secrets.

The callback accepts exactly one code and state. It consumes the transaction
before exchange, uses only configured HTTPS token and JWKS endpoints, and
accepts exactly RS256 with one matching public signing key of at least 2048
bits. Token exchange uses confidential-client HTTP Basic authentication and the
stored PKCE verifier. Signature, issuer, audience/authorized-party, subject,
nonce, expiry,
issued-at and authentication-time freshness, not-before, token type, and key
metadata fail closed. Authorization requests require fresh authentication with
`prompt=login` and `max_age=0`.

AAL2 is derived only when signed `acr` and `amr` claims both match configured
provider policy. A verified `(issuer, subject)` must already have an immutable
actor binding and a current teacher or course-admin membership. The callback
never creates an actor, identity binding, cohort, or membership.

## Sessions and CSRF

Successful staff authentication creates a random opaque `__Host-` cookie. Only
its SHA-256 digest is stored. Session rows bind the existing internal actor,
verified issuer/subject and assurance, a CSRF digest, idle expiry, absolute
expiry, and revocation state. Authentication re-resolves the immutable actor,
approved issuer, and current staff membership on every request. Internal hooks
revoke one session, all actor sessions, or all issuer sessions; separate
lifecycle hooks purge expired authorization material and inactive sessions.

Session and OIDC-transaction cookies are `Secure`, `HttpOnly`, `SameSite=Lax`,
host-only, and rooted at `/`. The independent CSRF cookie is `Secure`,
`SameSite=Strict`, host-only, readable by the same-origin client, and validated
against only its server-side digest. Every state-changing authenticated request
requires both an exact configured `Origin` and the session-bound CSRF header.
Logout also requires CSRF but remains available to an AAL1 staff session.
Privileged operations require current AAL2.

## HTTP boundary

`create_staff_transport_app` produces a Starlette ASGI application with:

- `GET /staff/oidc/login/{provider_id}`;
- `GET /staff/oidc/callback/{provider_id}`;
- `GET /staff/session` and `POST /staff/logout`;
- course-admin membership create/change/revoke endpoints;
- course-admin namespace claim, grant, grant-revoke, and transfer endpoints;
- one exact approved-registry read endpoint; and
- `POST /staff/pins`, the combined authoritative configuration-load and exact
  pin endpoint.

Operational requests require bounded correlation and actor-scoped idempotency
headers. JSON mutations reject duplicate keys, unknown fields, non-finite
values, invalid content types, and bodies over the configured limit. External
authentication, authorization/BOLA, conflict, validation, and framework errors
use bounded uniform JSON schemas. Security responses are non-cacheable and set
content-sniffing, framing, referrer, and default-deny CSP headers.

The control-plane transport is narrower than its underlying domain service:
membership roles and membership/namespace/grant/transfer targets must already
be staff. It cannot create or target a student role or serve as student
onboarding. Existing synthetic package records may still be projected and
pinned through the exact read-only server boundaries.

The pin request accepts exactly `configuration_locator`, `package_id`, and
exact `semantic_version`. The handler first calls the authoritative loader with
the opaque UUIDv4 locator, then passes only its sealed server-issued object to
the existing pinning service. It never accepts configuration identity, cohort,
digest, compatibility, package-set data, content, owner, artifact, approval
state, or approval identity.

## Persistence and production configuration

`SQLiteStaffTransportStore` is an additive reference schema and migration
boundary over the cumulative Phase E store. The ASGI composition lock makes its
single cross-thread reference connection deterministic. A production database
adapter must preserve one-time transaction consumption, opaque session digests,
expiry/revocation, Phase E foreign keys, optimistic comparisons, append-only
domain evidence, and atomic domain transactions.

Provider endpoints, client credentials, allowed origin, AAL claim mappings,
cookie names, TTLs, clock skew, token age, and body/response limits are supplied
through `StaffTransportConfig`. Production composition must obtain client
credentials from a secret manager and inject an `OIDCRemote`; no environment
loader, secret file, ASGI server, proxy, TLS terminator, or deployment is added
by this slice.

Only pre-seeded synthetic/non-minor records are authorized for this tranche.

## Explicit exclusions

This slice adds no package submission/upload route, student account or
onboarding, real-minor-data handling, review UI/route, registry listing/search,
configuration authoring/mutation, signing, deployment, moderation, or
student-code execution.
