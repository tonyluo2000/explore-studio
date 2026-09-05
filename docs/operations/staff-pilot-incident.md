# Staff Pilot Incident Response

This runbook applies only to the synthetic/non-minor staff pilot.

1. Stop new ingress at the pilot proxy without changing the datastore.
2. Record the incident identifier and time outside request logs. Do not copy
   cookies, tokens, authorization codes, subjects, locators, or secrets into
   tickets or chat.
3. For an actor compromise, invoke `StaffPilotMaintenance.revoke_actor`. For an
   issuer or client compromise, invoke `revoke_issuer`, disable the OIDC client
   at the provider, and follow the secret-rotation runbook.
4. Confirm `/health/live`; treat `/health/ready` failure as unavailable without
   extracting database details through HTTP.
5. Preserve the immutable audit records and a restricted copy of the synthetic
   datastore. Do not update or delete audit rows.
6. Review only redacted route/status metrics and correlation tags. Retrieve
   detailed evidence through an approved, audited offline process.
7. Restore ingress only after credentials, issuer configuration, proxy CIDRs,
   synthetic classification, revocation, and a complete staging login-to-pin
   check have been independently verified.

If any real-minor data is discovered, stop the pilot and escalate immediately;
this system is not approved to process that data.
