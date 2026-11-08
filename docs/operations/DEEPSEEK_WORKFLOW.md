# Cross-project implementation and review workflow

Final owner policy, November 7, 2026: Codex and Claude are primary.
DeepSeek Pro requires an explicit owner request; quota constraints never
select it automatically.
Earlier Flash/Pro-first defaults are superseded. Unknown quota never activates a paid provider.
Use `scripts/agent-route.mjs`; see `MODEL_ROUTING.md` for execution, quota,
escalation, telemetry and the separate activation gate. The owner and existing
Claude release captain retain their authority. A router cannot relax reviews.

The separate `scripts/deepseek-agent.mjs` profile proposes bounded changes and
supports isolated worktrees, local focused tests and draft PR preparation.
See `DEEPSEEK_IMPLEMENTER.md`. It does not change shared Codex/Claude settings.
The existing `scripts/deepseek-review.mjs` pipeline retains complete immutable
comparison accounting, exact base/HEAD binding and durable review state. See
`DEEPSEEK_TRANSFER_POLICY.md` and `DEEPSEEK_BUDGET.md` for the transfer and
shared accounting boundaries. All paid transport is disabled pending reviewed
activation; mock reports grant no review, merge or deployment authority.

## One operator entry point

Use `scripts/deepseek.mjs` for both roles. Preparation performs bounded source
checks and writes one compact, non-authorizing decision card. It sends no model
request and installs no standing policy:

```sh
bash scripts/with-project-node.sh node scripts/deepseek.mjs prepare --task /absolute/task.json --card /absolute/private/card.json
```

The task uses `cross-project.deepseek-operator-task.v1`, an approved repository,
`implementation` or `review`, exact base/head, a task ID, risk and an explicit
low/high effort. Implementation supplies bounded owned/context paths and its
owner-selected test plan. Review supplies the PR number and known author family.
The card shows the complete inventory, destination, request/body SHA-256,
application choice and maximum cost. Its owner-request, transfer and payment
flags start false. A prepared card or a prior call is never consent.

After the existing owner process approves that exact card, execute with the
same task and the reusable reviewed standing-policy record:

```sh
bash scripts/with-project-node.sh node scripts/deepseek.mjs execute --task /absolute/task.json --card /absolute/private/card.json --standing-policy /absolute/private/policy.json --output /absolute/private/result.json
```

Approval files must be private, regular files outside the source checkout.
Execution rechecks scope, source, body, effort, limits and policy identity, then
uses the fixed durable role runner. There are no paid retries or fallback.
The underlying owner/call grants are derived in memory; the operator does not
prepare separate redundant manifests. No real standing record is installed by
setup, a source-only task, or a mock. The final source profile must retain its
required independent security qualification before activation.

Implementation proposals remain isolated and report `APPLIED_UNTESTED` when
applied. Codex reviews the diff, runs only the owner-selected focused test plan
through the normal sandbox/project launcher, and integrates under existing
review and CI gates. Suggested argv is data; arbitrary model-generated commands
are never run automatically. Full provider/usage receipts preserve possible
transfer and charge state on incomplete or ambiguous responses.

Hosted review uses the existing owner-dispatched Mile Commons workflow and its
one JSON request, not the local combined executor. It reserves and persists its
receipt before the provider credential is exposed. Local key absence does not
block this hosted path. The default workflow token covers Mile Commons and
public Explore Studio; private MonteFinance remains permission-blocked unless
an existing approved repository-reading credential is available. Do not export
the hosted key or ask for it in chat. Local implementation uses the original
credential through the documented secure custodian provisioning step.

## Project constraints

- Mile Commons: native V1, workout sync, account lifecycle, events/clubs/routes,
  Race Day and Photo P6 remain priorities. Health, runner identity, GPS and
  private photos/club records cannot be transferred. Terms/source-integrity,
  native beta and release-captain gates remain binding.
- MonteFinance: simulation correctness, scenarios, Advisor API, frontend and
  numerical/security tests remain priorities. Financial calculation changes
  require deterministic seeded tests and independently specified numerical
  baselines. A model verdict never substitutes for mathematical verification.
  No account records, private simulations or financial data may be transmitted.
- Explore Studio: routine code, course tools, documentation/tests and UI may
  use the profile within licensing/content ownership and learner privacy
  controls. No automatic content publishing or releases.

All three repositories vendor the same versioned adapter snapshot. The
toolchain inventory identifies its source SHA and per-file SHA-256 hashes;
update snapshots together through source-only PRs, while project path adapters
remain explicit in the shared policy. No third-party package installation or
additional provider client is needed.

## Offline qualification

Where a Node launcher exists, prefix these commands with
`bash scripts/with-project-node.sh`. Other projects use Node 22.13.0 or newer.

```
node --test tests/deepseek-*.test.mjs tests/model-*.test.mjs tests/agent-route.test.mjs
```

Mile Commons additionally retains `npm run test:deepseek-review`. Mandatory
repository FULL CI belongs on the stable qualified PR head under existing
policy. Focused local checks do not confer merge readiness.

## Seven-day measurement after authorized activation

Record T0 only after policy review, project-specific transfer and distinct
payment approval, approved credentials, and both live qualification calls:
one small real implementation and one review of a Codex-authored change.
Keep live calls serialized and retain their exact receipts. This implementation
does not itself authorize either qualification call.

Compare [T0,T0+7 days) to reliable preceding-week observations. Track project,
PR/task, task class, actual provider/model, input/output/cache tokens, preflight
reservation, estimated token cost, provider charge when available, duration,
success/failure, findings, acceptance/rework, merged functionality and resolved
defects. Record Claude/Codex quota interruptions and CI runner-minutes where
observable. Use `scripts/deepseek-usage.mjs` to report and annotate outcomes.
Missing values remain unknown; no savings or throughput improvement is claimed
without comparable observations. Each budget pool serializes its own paid
calls. Run at most two local substantive lanes plus an isolated lightweight
documentation lane. Keep agents assigned to active work and comparisons offline
unless the owner authorizes a paid call.

Current API pricing and exact model IDs were checked against the provider's
[official pricing](https://api-docs.deepseek.com/quick_start/pricing/) and
[Chat Completions contract](https://api-docs.deepseek.com/api/create-chat-completion/)
on November 7, 2026. Routine DeepSeek effort is explicitly `low`; its API maps
`medium` to `high`. Reverify prices before a new activation period.
