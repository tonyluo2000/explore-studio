# Cross-Project CI Batching Policy

Applies to Mile Commons, MonteFinance, Explore Studio and every future project.
Owner-approved 2026-11-17. Slogan: **Review individually. Test locally. Qualify together. Merge safely.**

## Rules

1. **Batch by default.** Compatible, independently reviewed PRs are combined into one integration branch cut from current `main`, merged in dependency order. One PR per CI run is the exception, not the default.
2. **Test locally first.** Before a batch is pushed for qualification, run on the Mac: typecheck, lint, the changed suites, every shared-boundary or inventory guard the changed paths can reach (tree-scanning allowlists, route/ingress/boundary matrices, localization/analytics guards, Terms-exclusion maps), and the local affected-tests selector when available. Local results are evidence only; they never satisfy a required check, review or approval.
3. **One authoritative full hosted CI per batch.** The full hosted gate runs once, at the final integrated head, not once per source PR. A push that changes the head invalidates earlier evidence; batch corrections instead of pushing one fix per run.
4. **Preserve traceability and gates.** Every source PR keeps its own review verdict at its own head. The batch PR lists each source PR, its head SHA, its review verdict and its owner GO. Critical, security, privacy, authorization and Terms reviews stay independent and cross-model where already required. Owner approval is recorded per merge at the exact batch head. After merge, source PRs are closed as incorporated with a link to the batch.
5. **Keep apart what must stay apart.** Do not batch: unrelated Critical changes, migrations and anything that applies production state, changes needing incompatible approvals, a change that edits the same legal/authorization guard in conflicting ways, or any PR without a current-head review. A change that fails local qualification leaves the batch; it does not block the others.
6. **Coordinate automatically.** The coordinator forms batches, audits dependencies and overlapping files, holds the single merge slot, resolves shared-file conflicts once (union of independent additions only; never loosen a guard), and posts the plan on the merge-queue issue. `scripts/ci-batch-plan.mjs` produces the audit and the metrics; it is a helper, not a new CI system.
7. **Never weaken coverage or protection.** No removed or skipped tests, no relaxed branch protection, rulesets, required checks, Terms/legal guards or review requirements to save minutes. A proposed reduction in mandatory hosted coverage needs separate owner approval with evidence.
8. **Measure.** Track per period: hosted runs avoided, billed minutes saved, failed hosted runs (and whether local checks could have caught them), merge-to-delivery time, and CI cost per delivered feature. Target: at least 50% lower hosted CI cost per delivered feature than the pre-policy baseline.

## Batch checklist

1. List candidate PRs; each needs a review verdict at its current head.
2. Audit stacks (base branches), overlapping files and shared guard/exclusion files.
3. Build `integration/<name>` from current `main`; merge in dependency order; rebase stale stacks first.
4. Resolve shared-file conflicts once; keep every guard at least as strict.
5. Run local qualification (rule 2). Drop PRs that fail.
6. Open the batch PR listing source PRs, heads, verdicts and GOs; take the merge slot; one hosted run.
7. Obtain the owner GO at the exact batch head; merge; close source PRs as incorporated; release the slot.
8. Record the metrics.
