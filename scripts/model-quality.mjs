// Shared quality floors. A quota shortage never changes these requirements.
const RISKS = new Set(['low', 'medium', 'high', 'critical']);
const EFFORTS = ['low', 'medium', 'high'];
const SHA = /^[a-f0-9]{40}$/;
const fail = code => { throw Object.assign(new Error(code), {code}); };

export function qualityRequirements({risk, complexity, taskType, history = {}} = {}) {
  const normalizedRisk = typeof risk === 'string' ? risk.toLowerCase() : 'unknown';
  const effectiveRisk = RISKS.has(normalizedRisk) ? normalizedRisk : 'high';
  const reasons = [];
  let minimumEffort = 'low';
  if (!RISKS.has(normalizedRisk)) reasons.push('UNKNOWN_RISK');
  if (['high', 'critical'].includes(effectiveRisk)) reasons.push('HIGH_RISK');
  if (['standard', 'complex', 'multi-file'].includes(complexity)) minimumEffort = 'medium';
  if (['architecture', 'difficult', 'difficult-debugging'].includes(complexity) || taskType === 'architecture') reasons.push('ARCHITECTURE');
  if (!Number.isSafeInteger(history.failedAttempts ?? 0) || (history.failedAttempts ?? 0) < 0) fail('INVALID_FAILURE_HISTORY');
  if ((history.failedAttempts ?? 0) >= 2) reasons.push('TWO_FAILED_ATTEMPTS');
  const triggers = {
    repeatedDefect: 'REPEATED_DEFECT',
    criticalInvariantFailed: 'CRITICAL_INVARIANT_FAILED',
    correctnessUncertain: 'CORRECTNESS_UNCERTAIN',
    securityUncertain: 'SECURITY_UNCERTAIN',
    privacyUncertain: 'PRIVACY_UNCERTAIN',
    financialUncertain: 'FINANCIAL_UNCERTAIN',
    substantiveReviewDefect: 'SUBSTANTIVE_REVIEW_DEFECT',
  };
  for (const [key, reason] of Object.entries(triggers)) {
    if (history[key] !== undefined && typeof history[key] !== 'boolean') fail('INVALID_FAILURE_HISTORY');
    if (history[key]) reasons.push(reason);
  }
  // Task labels can raise a caller's classification, never lower it.
  const sensitive = ['security', 'privacy', 'financial', 'tax', 'authorization', 'migration', 'release-tooling'].includes(taskType);
  if (sensitive && !reasons.includes('HIGH_RISK')) reasons.push('HIGH_RISK');
  if (reasons.length) minimumEffort = 'high';
  const independentReviewRequired = ['high', 'critical'].includes(effectiveRisk) || sensitive
    || !!(history.criticalInvariantFailed || history.securityUncertain || history.privacyUncertain || history.financialUncertain || history.substantiveReviewDefect);
  const gates = ['PROJECT_CI_REQUIRED', 'PROJECT_SECURITY_GATES_REQUIRED'];
  if (independentReviewRequired) gates.push('EXACT_HEAD_REVIEW_REQUIRED', 'INDEPENDENT_DIFFERENT_FAMILY_REVIEW_REQUIRED');
  if (effectiveRisk === 'critical') gates.push('OWNER_RELEASE_APPROVAL_REQUIRED');
  return {risk: sensitive && effectiveRisk !== 'critical' ? 'high' : effectiveRisk, minimumEffort, independentReviewRequired, reasons, gates};
}

export function assertQualityFloor({requestedEffort, effectiveEffort = requestedEffort, requirements}) {
  if (!requirements || !EFFORTS.includes(requestedEffort) || !EFFORTS.includes(effectiveEffort)
    || !EFFORTS.includes(requirements.minimumEffort)) fail('INVALID_QUALITY_EFFORT');
  if (EFFORTS.indexOf(effectiveEffort) < EFFORTS.indexOf(requirements.minimumEffort)) fail('QUALITY_FLOOR_NOT_MET');
  return true;
}

function identityFamily(identity) {
  // These prefixes identify model families; aliases such as "codex" and
  // user-supplied family labels are not evidence of an actual runtime model.
  const model = identity?.actualModel;
  if (typeof model !== 'string') fail('ACTUAL_MODEL_IDENTITY_REQUIRED');
  let family;
  if (identity.provider === 'openai' && /^gpt-[0-9][a-z0-9.-]{0,79}$/.test(model)) family = 'openai';
  if (identity.provider === 'anthropic' && /^claude-(?:haiku|sonnet|opus)-[0-9][a-z0-9.-]{0,79}$/.test(model)) family = 'claude';
  if (identity.provider === 'deepseek' && /^deepseek-(?:v[0-9][a-z0-9.-]*|flash)$/.test(model)) family = 'deepseek';
  if (!family || identity.family !== undefined && identity.family !== family) fail('INVALID_MODEL_IDENTITY');
  return family;
}

export function assertIndependentReview({implementation, review, headSha, baseSha}) {
  if (!SHA.test(headSha ?? '') || !SHA.test(baseSha ?? '')) fail('EXACT_COMPARISON_REQUIRED');
  const implementedFamily = identityFamily(implementation);
  const reviewedFamily = identityFamily(review);
  if (implementedFamily === reviewedFamily) fail('INDEPENDENT_MODEL_REQUIRED');
  if (review.headSha !== headSha || review.baseSha !== baseSha
    || implementation.headSha !== headSha || implementation.baseSha !== baseSha) fail('STALE_REVIEW_COMPARISON');
  if (review.outcome !== 'clean' || review.substantiveDefects !== 0) fail('CLEAN_REVIEW_REQUIRED');
  if (review.participatedInImplementation !== false) fail('REVIEWER_AUTHORSHIP_UNRESOLVED');
  return {independent: true, implementationFamily: implementedFamily, reviewerFamily: reviewedFamily, headSha, baseSha};
}
