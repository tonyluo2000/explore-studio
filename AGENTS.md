# Explore Studio model workflow

Use the owner-authorized project/task routing in
`config/ai-model-routing.json` and `docs/operations/DEEPSEEK_WORKFLOW.md`.
DeepSeek Flash is preferred for routine edits, docs and tests; Pro for ordinary
implementation and review of another model family's work. Codex coordinates
overlapping changes. Claude remains available for critical security and
architecture review. Same-family reviews do not establish model independence.

The separate guarded CLI does not replace Codex/Claude global configuration.
All new source-transfer eligibility remains mock-only until independent review
and separate exact-call source-transfer/payment authorization. Live budgets
are ceilings, never spending approval. Use Node 22.16.0 or newer for the
standalone dependency-free tooling tests documented in the workflow.

Preserve licensing, content ownership, private learner-data and publishing
controls. Never send learner records, private submissions, photos, credentials
or generated artifacts to external models. Do not automatically publish
content, merge or release. Focused tests and a model report do not replace
existing human approval or project CI requirements.
