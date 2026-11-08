# Cross-project source transfer qualification

Status: implemented for offline qualification; **live transmission disabled**.
Owner role decisions: Mile Commons #1120 and MonteFinance #980 (November 7,
2026). Those decisions do not replace existing exact-call transfer, spending,
security-review, merge, Terms, release-captain, financial, or publishing gates.

The shared `scripts/deepseek-transfer-policy.mjs` has three exact repository
adapters. `projectPathPolicy(repository, filename)` fails closed on unknown
repositories, unknown paths, escaped or noncanonical paths, secrets, private
record/media/export directories, binaries, and generated output. It does not
provide a general `mobile/**` rule. Mile Commons permits `mobile/App.tsx`,
listed package/app/compiler configuration, TypeScript in `mobile/src/`,
`mobile/tests/`, and `mobile/__tests__/`. The candidate Swift rules are
`mobile/ios/MileCommons/` and `mobile/ios/MileCommonsTests/`; candidate Kotlin
rules are the `com/milecommons` main/test package directories. These native
paths are provisional classifications requiring independent review against
the actual native branch; they grant no live-transfer authority. Other native
build/config files remain denied until separately classified.

MonteFinance permits scoped Python backend and frontend source, scripts,
tests, documentation and its existing DeepSeek instruction directory. It
excludes actual financial/account/private simulation records. Deterministic
numerical baselines remain mandatory independently of model judgments.
Explore Studio permits engine, library, course website source, course template,
scripts, tests and documentation; student submissions and private learner data
remain denied. Licensing, ownership and publication decisions stay human.

`assertSafeSource` rejects recognized credentials and suspicious high-entropy
values in full implementation context. Review continues to redact known
credentials and refuses remaining unknown entropy. Recognizable personal,
health, location and financial records fail before prompt construction,
including in PR titles and bodies. Scanning cannot establish the absence of
arbitrary private data: a human must still classify every intended source
input for each authorization. Synthetic tests use inline invented values;
existing fixture/evidence directories are not silently reclassified.

`readSafeSource` reads bounded UTF-8 regular files only, rejects symlinks in the
repository root and path components, uses `O_NOFOLLOW` for the final file, and
checks identity before returning source. The immutable Git comparison also
rejects symlink file modes and rename/copy source reclassification. Complete
changed-file and changed-line accounting remains required; one denied file
refuses the whole review. No source relocation, partial review, or omission
can make a blocked delta eligible.

Request policy v5 binds transfer-policy version, repository, PR/task role, base,
HEAD, authorization ID, requested model/effort, exact body and limits in receipts.
Paid profiles accept only `deepseek-v4-pro`; returned model must match. Effort
is explicitly low or high, never medium. Every request has zero retries and a
maximum $1 cap, plus the host-shared $10 rolling-week ledger. A reused request
or owner authorization ID is rejected across projects even after that window.
Existing stricter qualified profiles remain binding. Hosted Actions fails closed
without shared accounting. Usage is retained on an incomplete response only
when provider identity and counters validate; a partial verdict is never accepted.

Live capability activation requires independent Claude review of the executable
source-policy digest and a separate owner-approved activation record. The
`--activation FILE` input is validated by `model-activation.mjs`; there is no
boolean or environment switch. Source adapters describe this policy and never
claim that a record is installed. Any protected source change invalidates the
record. Activation is reusable only while that source digest stays unchanged;
it grants neither a fresh task request nor exact-call transfer/spending consent.
Those remain separate scoped inputs for every call. No activation record is
created or enabled by this change. Credentials are not created, copied or
printed. Mock evidence remains `MOCK_ONLY` and `REVIEW_NOT_COMPLETE`, never a
provider review or merge/release approval. Scan-only source classifications are
reported separately from actual transmitted-data redactions.

Focused qualification:

```bash
bash scripts/with-project-node.sh node --test \
  tests/deepseek-review.test.mjs tests/deepseek-transfer-policy.test.mjs
```

No live request or external source transmission is needed for these tests.
