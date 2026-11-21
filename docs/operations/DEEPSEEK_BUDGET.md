# Shared DeepSeek accounting

The guarded transport reserves the entire approved request ceiling before it
can send a request. Hard limits are $1/request and $10 over the preceding 168
hours, across all three approved repositories. The rolling window is stricter
than a calendar-week reset. Existing $0.02/$0.15/$0.30 review profiles still
apply. A cap grants no payment or source-transfer authorization.

All local copies use the same fixed store:
`~/.local/state/deepseek-workflow`. There is no CLI or environment override.
The `ledgerDirectory` library option exists for isolated offline tests, not
operator routing. Separate OS accounts/hosts are not a shared budget authority;
use one designated local execution host. GitHub Actions paid transport fails
closed with `SHARED_LEDGER_UNAVAILABLE`. A common transactional accounting
service is required before enabling multiple paid hosts.

The transport holds one exclusive directory lock across each request. Events
are exclusive-created, fsynced, read-only, chained by SHA-256, and contain no
source or raw provider output. Corruption blocks further calls. A crashed
process leaves its lock in place. Do not automatically clear a lock or refund
a reservation after timeout, cancellation, invalid response or ambiguous
failure. Reconcile provider activity before manually recovering an abandoned
lock. Request identities cannot be reused. These controls assume a trusted
operator and protected local state; the OS account owner can modify its files.

Reservations retain their full ceiling even after a cheaper successful call.
This conservative accounting can stop useful work early, but cannot silently
increase spending authority. Amounts are accounted as rounded-up microdollars.
Reported token-derived cost uses peak rates and is an estimate; provider-billed
charges remain `null` until reconciled externally. Missing cache counters are
unknown, never fabricated zeroes.

Run through the project's Node launcher where present:

```
node scripts/deepseek-usage.mjs report
node scripts/deepseek-usage.mjs outcome REQUEST_SHA256 accepted no-rework '{"P0":0,"P1":0,"P2":0,"P3":0}'
```

Outcome annotations append acceptance, rework and finding counts without
rewriting the provider receipt. Release authority is always `NONE`. Use the
seven-day measurement procedure in `DEEPSEEK_WORKFLOW.md`; savings are unknown
until both baseline and comparison observations exist.
