# Staff Pilot Rollback

1. Stop the single ASGI worker and confirm the `.pilot.lock` is released.
2. Verify the absolute datastore path and environment ID against the deployment
   record. Never use a broad path, glob, or unresolved environment variable.
3. Preserve a restricted synthetic datastore snapshot and the deployed config
   digest. Do not export OIDC secrets with either artifact.
4. Restore the last reviewed wheel and non-secret configuration. The pilot
   marker schema is additive; the prior staff transport ignores it.
5. Keep the same database only when the restored code supports every recorded
   Phase E schema version. Otherwise provision a fresh classified synthetic
   database and follow the reset runbook.
6. Restart exactly one non-preloaded, non-reloading worker with ASGI lifespan
   enabled and construct the runtime inside that final process. Then verify
   liveness, readiness, login/session,
   CSRF rejection, one control-plane transition, exact registry read, sealed
   configuration load/pin, logout, and issuer revocation.
7. Reopen ingress only after those checks and the redacted operational log have
   been reviewed.

Rollback never rewrites immutable packages, configurations, pins, idempotency
records, or audit evidence.
