# Task-level model selection

Owner instruction: **“we will explicitly say use deepseek pro, otherwise,
always use codex or claude.”** This supersedes previous Flash-first and
quota-triggered standby proposals. Neither a low allowance nor exhausted
subscription capacity may automatically select a paid DeepSeek request.

The dependency-free `scripts/deepseek-routing.mjs` exports `resolveRoute`.
`config/ai-model-routing.json` defines project and task defaults. The shared
snapshot includes capability, quota-evidence and quality-floor modules; each
project receives identical core files with its own repository identity.
The full primary-agent CLI wrapper belongs to the separately coordinated
integration and is not included in this change. Global Codex/Claude settings
remain untouched.

Default decisions select Codex or Claude. Routine documentation and small
tasks use low effort; ordinary work uses low/medium. Architecture, difficult
debugging, high risk, uncertainty and grounded repeated failures raise effort.
Unknown risk defaults upward. Unsupported models, invented capability labels
and unknown effort settings fail closed. Capabilities may narrow the verified
catalog; they cannot introduce a new provider or weaken its quality floor.

A request for DeepSeek requires both explicit owner intent and the exact Pro
model identifier:

```js
resolveRoute({
  repository: 'tonyluo2000/mile-commons',
  taskType: 'implementation',
  risk: 'low',
  ownerRequestedDeepSeek: true,
  overrides: { model: 'deepseek-v4-pro' }
});
```

The returned reason is `EXPLICIT_OWNER_REQUEST`. This request may be selected
with healthy, unknown or constrained primary quota because the owner asked
for it. It still cannot authorize source transfer, spending or release.
DeepSeek Flash is not selectable. DeepSeek effort is explicitly low or high;
a requested medium effort is rejected because the provider maps medium to
high. Task-required medium effort without an explicit effort override is
raised to high when Pro is explicitly selected.

Quota evidence defaults to unknown. Fresh owner/provider reports can inform
primary capacity selection. If a primary is exhausted or rate limited, the
router may choose another suitable Codex/Claude model or fail. It never picks
DeepSeek from quota evidence alone. Quota pressure does not reduce reasoning,
review, tests or any quality requirement. Model selection happens before a
task and does not switch a running task or retry paid requests.

Reviews require a different model family from the implementer. Two DeepSeek
reviews, including Flash versus Pro, are not independent-model reviews.
Reviewer suggestions remain Codex/Claude and become blocked if no suitable
required primary reviewer is available. Explicitly selecting DeepSeek for a
review cannot bypass same-family refusal. High/Critical changes retain
independent exact-head review; financial calculations still need deterministic
numerical verification. Existing CI, privacy, Terms, publishing and owner /
release-captain gates remain binding. `taskType:'release'` returns existing
human authority and no model.

The guarded implementation/review commands accept an explicit routing context
with `ownerRequestedDeepSeek:true`; the transport revalidates owner intent and
pins the approved serialized request body. Proposals and mock receipts do not
prove a live model ran. Actual model and usage must come from the provider.

`LIVE_TRANSFER_ENABLED` remains false. Independent transfer-policy review,
reviewed activation, exact-call source/payment approval and approved credentials
are distinct requirements. The $1/request and $10/shared-week ceilings limit
spending; they do not authorize a call. Unknown paths, incomplete diff
inventories, private records, secrets, high-entropy values, symlink escapes,
unsigned source classification or stale HEAD/base still stop transmission.

Run focused offline routing validation through the required runtime launcher:

```sh
bash scripts/with-project-node.sh node --test tests/deepseek-routing.test.mjs tests/model-quality.test.mjs tests/model-quota.test.mjs
```

Account/capability and quota evidence remain separate from actual execution.
No source transfer or paid model call occurs during routing validation. Measure
usage, charges, rework and delivered outcomes after separately authorized
activation; do not claim savings from route selection or mock tests.
