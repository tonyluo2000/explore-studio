# Staff Pilot Synthetic Data Reset

1. Stop ingress and the single worker; confirm the process lock is released.
2. Verify twice that the exact absolute target is the recorded staff-pilot
   `.sqlite3` path and that its immutable marker says `synthetic-non-minor` with
   the expected environment ID. Stop if either check fails.
3. Move the database and its adjacent `.pilot.lock` into a restricted quarantine
   location under the pilot retention procedure. Do not recursively delete a
   directory and do not delete rows from append-only tables.
4. Bootstrap the same absolute path through
   `bootstrap_synthetic_pilot_datastore`; this recreates cumulative migrations,
   file permissions, the process lock, and the immutable classification marker.
5. Seed only reviewed fictional actors, cohorts, packages, approvals, and
   configurations. Do not import production, school, guardian, or student data.
6. Run the complete staging login/session/CSRF/control-plane/registry/load/pin
   scenario, logout, issuer revocation, cleanup, and readiness checks.
7. Record the old/new datastore fingerprints and operator approval without
   recording identities, tokens, locators, package contents, or secrets.

Any uncertain or mixed-classification datastore must be quarantined and never
adopted by the pilot bootstrap.
