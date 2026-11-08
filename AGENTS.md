# Explore Studio model workflow

November 7, 2026 final owner rule: always use Codex or Claude unless the
owner explicitly requests DeepSeek Pro. Quota pressure, rate limits and cost
never automatically select DeepSeek. See `config/ai-model-routing.json` and
`docs/operations/MODEL_ROUTING.md`. Source transfer remains disabled pending
independent review and separate exact-call transfer/payment authorization.
All existing human review, privacy, financial verification and release gates
remain mandatory.

The separate guarded CLI does not replace Codex/Claude global configuration.
All new source-transfer eligibility remains mock-only until independent review
and separate exact-call source-transfer/payment authorization. Live budgets
are ceilings, never spending approval. Use Node 22.13.0 or newer for the
standalone dependency-free tooling tests documented in the workflow.

Preserve licensing, content ownership, private learner-data and publishing
controls. Never send learner records, private submissions, photos, credentials
or generated artifacts to external models. Do not automatically publish
content, merge or release. Focused tests and a model report do not replace
existing human approval or project CI requirements.
