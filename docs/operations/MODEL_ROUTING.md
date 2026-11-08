# Task-level model selection

Final owner policy, November 7, 2026: Codex and Claude first. DeepSeek Pro is
explicit opt-in only. The latest direct owner instruction supersedes both
Flash/Pro-first defaults and quota-triggered standby: “we will explicitly say
use deepseek pro, otherwise, always use codex or claude.”
Earlier backup policy references (superseded on automatic activation): [Mile Commons #1120](https://github.com/tonyluo2000/mile-commons/issues/1120#issuecomment-6715998366),
[MonteFinance #980](https://github.com/briersystems/montefinance/issues/980#issuecomment-6715998814).

The dependency-free reference implementation is maintained in Mile Commons and
vendored identically into the other repositories. `config/model-project.json`
is the small project adapter; `config/deepseek-toolchain.json` pins the shared
snapshot with SHA-256 hashes. Update this common snapshot together, not separate
router forks. No global Claude/Codex configuration is changed.

## Selection and execution

Use Node through the repository launcher where supplied:

```sh
bash scripts/with-project-node.sh node scripts/agent-route.mjs --task /absolute/task.json --output /absolute/decisions.jsonl
```

Other repositories use a compatible Node runtime; no dependency install is
needed. The task JSON contains `repository`, a non-sensitive `taskId`,
`headSha` (the exact current commit), `taskType`, `risk`, `complexity`, optional
`history`, `implementerFamily` for review, and optional `overrides`. Use the
routing tests as the executable enum and quota examples. The adapter and
origin must match the requested repository. Unknown risk defaults upward.
`instruction` is read only when explicitly executing an approved primary task;
it never enters decision logs.

Selection is deterministic and does not call a model. `--execute` launches the
selected installed primary CLI only when a separately supplied, reviewed owner
activation record validates. Adapter fields such as `primaryActivationRecordSchema`,
`activationPolicy`, `sourcePolicy` and `releaseAuthority` are descriptions, not
authority or switches. The wrapper reads the adapter repository identity and
checks the Git origin; the imported validator fixes the activation schema. Editing
an adapter cannot select another validator or grant execution. No activation
record is installed automatically. The CLI uses
explicit model and effort flags, starts one child, performs no retries and
never switches a successful task mid-run. DeepSeek selection is a handoff to
the guarded backup profile, not an unrestricted CLI invocation.

For a real no-source pilot, supply a task with `taskType: routine`, `risk: low`,
`complexity: simple`, no overrides/history and the current HEAD, then add
`--pilot`. This executes only a fixed synthetic Markdown formatting task with
read-only Codex permissions or disabled Claude tools. The input instruction is
ignored. Output is checked against `# Router pilot`. This proves task dispatch;
it does not activate repository-wide selection or transfer source to DeepSeek.

Requested model/effort are always recorded separately from actual identity.
If the CLI does not attest actual model or effective effort, those actual fields
remain null; a successful exit alone cannot verify them. Raw prompts, output,
CLI diagnostics and source do not enter the routing ledger.

## Quota evidence

Default quota is `unknown`. It permits suitable primary routing and never
activates paid backup. `--quota /absolute/quota.json` accepts a map keyed by
`codex` and `claude` with fresh owner/provider evidence. Reports expire; stale
reports become unknown. Remaining percentages are accepted only when actually
reported. The configurable low threshold defaults to 20 percent.

`--refresh-quota` performs one bounded Codex app-server
`account/rateLimits/read` request, without a model turn. The collected report
can include daily/session/weekly windows as returned; rate limiting remains
distinct from exhaustion. No daemon, timer or repeated polling is installed.
Claude's documented `/usage` is interactive; the router does not scrape private
account endpoints, read credential stores or invent weekly balances. Use a
fresh explicit owner report when machine-readable visibility is unavailable.

Low/exhausted/rate-limited evidence never selects DeepSeek. Suitable Codex/Claude
capacity is selected or the task is held. `--owner-request FILE` is required for
explicit Pro selection, including when primary quota is healthy or unknown.
The operator file uses `cross-project.deepseek-owner-request.v1` and binds
repository, taskId, implementation/review role, exact base/HEAD, Pro model,
non-sensitive authorization ID/reference and issue/expiry timestamps (at most
24 hours). A config override, boolean, task-manifest field or previous task
request cannot substitute for this fresh, separately supplied owner input.
Missing source/payment authorization still blocks transmission. Owner model
overrides remain subject to verified capabilities, minimum risk/effort and
independent-review rules. The task JSON cannot activate DeepSeek by including
a model name or owner flag: only the separately supplied operator record is validated and forwarded.
These records are supplied by the trusted local operator through the existing
owner-approval process; they do not themselves authenticate a person.

## Quality, review and telemetry

Routine documentation uses low effort. Bounded code uses low/medium; difficult
work escalates. Two evidence-based failed attempts, recurring defects, critical
invariants, security/privacy/financial uncertainty, architectural complexity or
substantive review findings raise effort before provider changes when primary
capacity is available. High/Critical work requires high effort and independent
different-family review. Quota pressure cannot lower this floor.

`model-quality.mjs` validates independent review identities and exact base/HEAD
receipts. DeepSeek cannot review its own implementation; Flash versus Pro is
not independence. An unavailable required reviewer leaves a gate unsatisfied.
Model selection and a mock report cannot satisfy existing review, CI, Terms,
financial numerical verification, owner, publishing or release-captain gates.

`model-telemetry.mjs report /absolute/decisions.jsonl` summarizes the last seven
days of recorded decisions and supplied outcomes. Track observed tokens, quota
interruptions, provider charge, CI cost, rework, review findings and accepted /
delivered results. Unavailable measurements remain null, and coverage counts
make incomplete reporting visible. Attach outcomes only from test/review/delivery
evidence. No recurring paid measurement tasks are installed. Compare like task
classes with a measured baseline before claiming savings.

## Backup transfer and activation

`deepseek-agent.mjs --owner-request FILE --routing-context FILE` and
`deepseek-review.mjs --owner-request FILE --routing-context FILE` accept the
separate owner scope and classification context. The review task ID is
`pr-N-review`, derived from its actual pull number. `--source-root` enables
verified local exact-Git source classification for complete comparisons. See their `--help`
and tests for exact schemas. DeepSeek requests are Pro with explicit low/high;
medium and Flash are not automatic backup options. The transport revalidates
owner scope, per-call approvals, exact model identity and shared budget. A
`cross-project.deepseek-call-authorization.v1` record separately binds the owner
request ID and exact repository/task/role/base/head to request ID, serialized
body SHA-256, low/high effort, spending cap, expiry, and explicit source/payment
approval. Neither a request-size ceiling nor reviewer selection grants payment.
The shared ledger permanently refuses reuse of a request or authorization ID,
even for another project or a changed body. It holds the lock throughout the
paid request, retains ambiguous reservations and permits no automatic retries.

`PATH_NOT_ALLOWLISTED`, complete diff accounting, exact HEAD/base, source
classification, secrets/high-entropy scanning, size/token bounds and all private
data exclusions remain binding. Native TypeScript, Swift and Kotlin eligibility
uses explicit prefixes/extensions; there is no blanket `mobile/**` permission.
Never rename, move or omit a blocked file to evade a guard.

Only the three exact routing configuration paths are eligible; `config/**`
remains denied. Local classifications verify repository identity, immutable
base/HEAD and the complete raw file section before treating finite known source
tokens, verified toolchain digests or individually classified synthetic test
spans as source. No file is omitted; unknown opaque values and real private
records remain denied.

No activation is installed by default. `--activation FILE` consumes a separate
operator record with the exact executable source-policy digest, owner approval
reference and a clean independent Claude review receipt identity. Source files
are hashed at use time; any control-code change invalidates activation. Primary
routing uses `cross-project.primary-routing-activation.v1`; DeepSeek capability
uses `cross-project.deepseek-activation.v1`. These records are separate and
neither grants a DeepSeek task request, source transfer or spending consent.
A qualified capability can thus be approved without changing source or starting
a new review/CI cycle. No activation file is created or enabled automatically.
Independent security review, capability activation and exact-call source/payment
approval remain distinct requirements. $1/request and $10/rolling-week caps are ceilings, not approval.
A pending router candidate does not authorize merge, paid calls, beta/production
activation, release, publishing or access around GitHub connector limitations.

## Verification and adoption

Run the shared offline suite from a stable candidate:

```sh
node --test tests/deepseek-*.test.mjs tests/model-*.test.mjs tests/agent-route.test.mjs
```

Use the repository launcher where required. These focused tests complement the
existing full project CI. Preserve all required project checks and exact-head
independent review before merge/activation. A validated synthetic pilot permits
only the bounded pilot; enabling the normal wrapper requires the existing owner
approval process. Measure week one from the first authorized normal task.

Capability sources checked November 7, 2026:
[OpenAI reasoning](https://developers.openai.com/api/docs/guides/reasoning),
[Codex app-server](https://learn.chatgpt.com/docs/app-server),
[Claude model configuration](https://code.claude.com/docs/en/model-config),
[Claude usage](https://code.claude.com/docs/en/costs),
[DeepSeek request contract](https://api-docs.deepseek.com/api/create-chat-completion/).
Installed CLI and account catalog evidence is checked separately; documentation
alone is not an account availability claim.

Authenticated historical reviews exhausted 1,000 output tokens. High-effort
review now refuses an output limit below 4,000 before dispatch. Qualified owner
call profiles may explicitly choose up to 16,000, within their approved dollar
ceiling; no retry or spending increase follows truncation. An incomplete or
invalid JSON response keeps the verdict incomplete while retaining validated
provider model/usage metadata. Raw output and reasoning text never enter receipts.
