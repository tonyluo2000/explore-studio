# Cross-project implementation and review workflow

Owner direction: November 7, 2026; Mile Commons #1120 and MonteFinance #980.
DeepSeek Pro is a first-class implementer and reviewer when reviewing another
model family's work. Flash handles routine work. Codex coordinates integration.
Claude remains available for critical architecture/security review and release
coordination. This updates model-role defaults, not review or release gates.

Executable routing lives in `config/ai-model-routing.json`; project entries may
override individual task defaults. `scripts/deepseek-routing.mjs` refuses
same-family independent review, including Flash reviewing Pro. It describes
escalations without automatically invoking or paying for another model.
Release authority always belongs to the existing owner/release captain.

The separate `scripts/deepseek-agent.mjs` profile proposes bounded changes and
supports isolated worktrees, local focused tests and draft PR preparation.
See `DEEPSEEK_IMPLEMENTER.md`. It does not change shared Codex/Claude settings.
The existing `scripts/deepseek-review.mjs` pipeline retains complete immutable
comparison accounting, exact base/HEAD binding and durable review state. See
`DEEPSEEK_TRANSFER_POLICY.md` and `DEEPSEEK_BUDGET.md` for the transfer and
shared accounting boundaries. All paid transport is disabled pending reviewed
activation; mock reports grant no review, merge or deployment authority.

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
`bash scripts/with-project-node.sh`. Other projects use Node 22.16.0 or newer.

```
node --test tests/deepseek-budget.test.mjs tests/deepseek-routing.test.mjs tests/deepseek-agent.test.mjs tests/deepseek-transfer-policy.test.mjs
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
without comparable observations. One paid call at a time; at most two local
substantive lanes plus an isolated lightweight documentation lane. No idle
agents or automatic paid comparison runs.

Current API pricing and exact model IDs were checked against the provider's
[official pricing](https://api-docs.deepseek.com/quick_start/pricing/) and
[Chat Completions contract](https://api-docs.deepseek.com/api/create-chat-completion/)
on November 7, 2026. Routine DeepSeek effort is explicitly `low`; its API maps
`medium` to `high`. Reverify prices before a new activation period.
