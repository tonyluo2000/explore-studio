# Isolated DeepSeek implementation profile

`scripts/deepseek-agent.mjs` is a separate direct-API profile. It changes no
Codex, Claude Code or Copilot global configuration. Routing is configurable
by project/task in `config/ai-model-routing.json`; overrides are explicit and
never grant paid-call authority. Codex/Claude are primary. This guarded Pro
profile requires an explicit owner request, supplied as
a fresh task-scoped `cross-project.deepseek-owner-request.v1` operator record
supplied by `--owner-request FILE`.
Neither model names nor quota constraints provide that opt-in. DeepSeek uses explicit low or justified high
reasoning, never medium. See `MODEL_ROUTING.md` for the final owner policy. DeepSeek reviewing DeepSeek is
refused as an independent-model review, including Flash versus Pro.

The host explores only explicitly listed source files at a pinned commit.
The provider proposes complete file replacements with original SHA-256 hashes.
It receives no shell, filesystem, GitHub, credential or release tools. Control-plane ownership is denied for agent/CI/configuration/package/guard files, without a bypass. Such files may supply eligible read-only context. The host
validates every replacement before applying any, requires a clean dedicated
`codex/deepseek-*` branch, locks the lane, refuses symlinks and stale content,
and reports operator-selected focused test commands without executing them. Model-authored code requires a separate operator review and sandboxed test step. Codex integrates overlaps.
Never reset another lane to make this profile start.

Create a task JSON outside the checkout or in an ignored output directory:

```json
{
  "schema": "cross-project.deepseek-implementation.v1",
  "repository": "tonyluo2000/mile-commons",
  "taskId": "bounded-source-fix",
  "taskType": "implementation",
  "title": "Describe the bounded source change",
  "instruction": "State acceptance criteria without private data.",
  "baseSha": "EXACT_BASE_SHA",
  "headSha": "EXACT_HEAD_SHA",
  "ownedPaths": ["lib/example.mjs"],
  "contextPaths": [],
  "tests": [{"kind": "node-test", "files": ["tests/example.test.mjs"]}],
  "maxCostUsd": 0.15,
  "maxRequestBytes": 64000,
  "maxOutputTokens": 4000
}
```

Use the repository runtime launcher:

```sh
bash scripts/with-project-node.sh node scripts/deepseek-agent.mjs \
  --task /absolute/task.json --output /absolute/outside-repository/preflight-1.json
```

`--create-worktree /absolute/new-lane --branch codex/deepseek-TASK` creates a
new lane at the manifest HEAD without copying any uncommitted files. Existing
branches/destinations are refused. A caller may instead prepare the isolated
lane separately. Mock mode never calls DeepSeek and cannot apply a patch.
`MOCK_ONLY` is neither implementation provenance nor an independent review.

Live calls remain blocked until independently reviewed transfer-policy
activation, approved credentials and exact-call source/payment authorization
are available. The separate `cross-project.deepseek-call-authorization.v1` approval binds the
owner authorization ID, task/repository/role/base/HEAD, serialized body SHA-256,
request ID, Pro model, explicit low/high effort, exact maximum cost, source and
payment approvals, timestamps and authorization reference. The mock preflight
provides request/body identity without a provider call. All scope changes or
body changes invalidate approval; the global ledger prevents authorization reuse.
The shared provider transport reserves against the cross-project ledger before
transmission; it permits zero retries and no fallback. Hosted calls without a
shared cross-host budget authority are disabled. Existing tighter envelopes
remain binding.

Once activated, `--live --approval /absolute/approval.json` prepares a validated
proposal. Add `--apply` to apply it with status `APPLIED_UNTESTED`. The agent never executes model-authored source or tests. Receipts omit raw
source and model output; proposal-only runs save a separate local `.proposal.json`
artifact for Codex integration. Receipts, identify requested/actual model separately, record
usage, and prepare a draft PR body without publishing it. Suggested test argv is recorded as `NOT_RUN`. A model response is not evidence that tests ran.
No merge, deployment, production activation, publishing or owner approval is
performed. Source-only implementation on a real task and a different-family
review still require separately authorized live qualification.

Suggested Node tests use `node --test` with explicit `tests/*.test.mjs` paths; Python tests
use `python3 -m pytest -q` with explicit `tests/*.py` paths. No model commands,
shell text or arbitrary CLI options are accepted. No test subprocess is launched by this profile. Review and execute focused tests separately in an appropriate sandbox.

An explicit absolute `--output` outside the checkout is required. Canonical, symlink-free receipt and proposal paths are reserved with exclusive mode-0600 files before any provider call; existing files refuse execution. Post-provider validation/application failures retain request identity and attested usage in the finalized receipt. Reports cannot overwrite previous receipts.
Provider accounting lives in the shared ledger; charges unavailable from the
provider remain `null`, rather than an invented billed amount. Record acceptance
and rework in the utilization ledger after independent review.
