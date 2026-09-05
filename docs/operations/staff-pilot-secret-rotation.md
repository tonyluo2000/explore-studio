# Staff Pilot OIDC Secret Rotation

1. Restrict ingress and revoke existing issuer sessions through
   `StaffPilotMaintenance.revoke_issuer`.
2. Create the replacement confidential-client credential at the approved OIDC
   provider. Do not place it in Git, a config file, command history, logs, or a
   ticket.
3. Update only the secret-manager/process injection addressed by the existing
   `env:EXPLORE_STAFF_SECRET_*` reference. The issuer, client ID, redirect URI,
   JWKS URI, and AAL mapping remain reviewed configuration.
4. Restart the one non-preloaded pilot worker so the secret is resolved once
   into a runtime constructed in that final process. Enable ASGI lifespan and
   remove the old process before enabling the replacement.
5. Complete authorization-code/PKCE login, AAL2 privileged denial/allowance,
   logout, and revocation checks with a synthetic staff identity.
6. Disable the prior credential at the provider and verify that it can no longer
   exchange a code.
7. Restore ingress and record only rotation time, operator, provider ID, config
   digest, and result—never either secret.

For suspected exposure, follow the incident runbook rather than using an
overlap window.
