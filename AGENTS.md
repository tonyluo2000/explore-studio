# Repository agent instructions

## Short GitHub tasks and permanent model/effort receipts

When given `owner/repo#number — execute`, read the referenced issue or PR,
its current head and existing acceptance criteria. Do not request a repeated
long prompt.

Select the lowest capable available model and reasoning effort for the task:
low for simple edits, docs and tests; medium for normal implementation and
debugging; high for difficult or security/privacy-critical work. Use Codex
for implementation by default and a distinct model family when independent
review is required. DeepSeek use remains subject to applicable source,
credential, and spending controls.

Every execution result **must contain a compact AI execution receipt posted
as a comment to the referenced GitHub issue or PR**: task, exact commit SHA,
role, requested provider/model/effort, actual provider/model/effort only when
runtime-attested (otherwise `unverified`), measured token usage and cost
where available (estimates clearly labeled), result/status and next blocker.
Keep it under ten lines and omit secrets, private data and raw prompts.
If posting is unavailable, disclose that persistence is not confirmed.

Preserve existing repo tests, code review requirements, publication controls
and release authorization. This instruction does not grant deployment rights.
