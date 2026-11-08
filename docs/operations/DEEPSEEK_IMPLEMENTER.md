# Isolated DeepSeek implementation

Use the shared `scripts/deepseek.mjs` operator entry point. Codex and Claude
remain primary; an explicit owner request is required for DeepSeek Pro.
Quota pressure, configuration overrides and earlier calls never supply consent.

Prepare a bounded task in a clean, dedicated `codex/deepseek-*` worktree:

```json
{
  "schema": "cross-project.deepseek-operator-task.v1",
  "repository": "tonyluo2000/mile-commons",
  "taskId": "bounded-source-fix",
  "role": "implementation",
  "taskType": "implementation",
  "risk": "low",
  "complexity": "routine",
  "reasoningEffort": "low",
  "title": "Describe the bounded source change",
  "instruction": "State acceptance criteria without private data.",
  "baseSha": "EXACT_BASE_SHA",
  "headSha": "EXACT_HEAD_SHA",
  "ownedPaths": ["lib/example.mjs"],
  "contextPaths": [],
  "tests": [{"kind": "node-test", "files": ["tests/example.test.mjs"]}],
  "applyChanges": false,
  "maxCostUsd": 0.15,
  "maxRequestBytes": 64000,
  "maxOutputTokens": 4000
}
```

The coordinator can create the isolated worktree through the existing Git
workflow. Never reset or clean another lane. `applyChanges` is part of the
approved task/card; it cannot be changed after approval. Context is limited to
tracked source at the exact HEAD plus explicitly owned new files. Private data,
secrets, symlinks, stale content and control-plane writes are refused.

```sh
bash scripts/with-project-node.sh node scripts/deepseek.mjs prepare --task /absolute/task.json --card /absolute/private/card.json
```

Preparation sends no provider request. The single decision card lists exact
source inventory, destination, model/effort, request/body digests, scope,
application choice and maximum cost. It starts unapproved. Once the owner
approves that exact call under the reusable reviewed standing policy:

```sh
bash scripts/with-project-node.sh node scripts/deepseek.mjs execute --task /absolute/task.json --card /absolute/private/card.json --standing-policy /absolute/private/policy.json --output /absolute/private/result.json
```

No separate owner-request and call-approval files are needed. The operator
revalidates source and derives those internal grants from the one approved
card. Approval/policy files and receipt paths must be private regular files
outside the source checkout. Existing receipts are never overwritten. The
production engine is stateful; direct stateless live exports refuse.

The provider can return only bounded owned-file replacements with original
SHA-256 hashes. It has no tools, shell, GitHub, credential or release access.
Responses are schema-checked before application. Isolated application reports
`APPLIED_UNTESTED`; a proposal artifact and owner-selected test argv are handed
to Codex. Codex reviews the diff and runs permitted focused tests through the
normal sandbox/project launcher. Model-authored commands and arbitrary shell
text are never executed automatically, and no test success is fabricated.

Durable receipts record possible transmission before fetch and receipt of a
response before parsing. Truncation, network/HTTP errors and invalid usage
retain conservative attempt state; only validated provider metadata can attest
actual model/usage. Unknown invoice charges stay null. Zero paid retries and
fallback, the $1 request ceiling or stricter profile, and the fixed $5 local
share of the $10/168-hour combined budget remain enforced.

Local execution uses the existing original credential through the secure
custodian provisioning procedure; never paste or export it in chat. Local key
absence does not disable the separate hosted review path. Source-only setup
installs neither real activation nor task/source/payment consent. Existing
independent-review, CI, privacy, financial, publishing and release gates remain
binding. No merge, deployment or production activation is performed.
