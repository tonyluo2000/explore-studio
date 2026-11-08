# Explore Studio model workflow

November 7, 2026 final owner policy: always use Codex or Claude unless the
owner explicitly requests DeepSeek Pro. Quota pressure and rate limits never
activate DeepSeek automatically. Use `scripts/agent-route.mjs` to choose the
lowest suitable primary model/effort; routine work must not default to Sol-high.
The separate `--use-deepseek-pro` operator flag records explicit selection only,
never source-transfer or spending approval. DeepSeek effort is low or justified
high, never medium. Independent different-family review, exact-head evidence
and all existing quality/release gates remain mandatory. Live DeepSeek transfer
stays disabled pending reviewed activation and exact-call authorization.
See `docs/operations/MODEL_ROUTING.md`.

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
