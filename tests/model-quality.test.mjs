import test from 'node:test';
import assert from 'node:assert/strict';
import {qualityRequirements, assertQualityFloor, assertIndependentReview} from '../scripts/model-quality.mjs';

test('low-risk routine work keeps a low quality floor and ordinary CI gates', () => {
  const requirements = qualityRequirements({risk: 'low', taskType: 'routine', complexity: 'simple'});
  assert.equal(requirements.minimumEffort, 'low');
  assert.equal(requirements.independentReviewRequired, false);
  assert.deepEqual(requirements.gates, ['PROJECT_CI_REQUIRED', 'PROJECT_SECURITY_GATES_REQUIRED']);
});

test('unknown risk fails upward and cannot be lowered through a caller effort', () => {
  for (const risk of [undefined, null, 'unspecified', 'LOWEST']) {
    const requirements = qualityRequirements({risk, complexity: 'simple'});
    assert.equal(requirements.risk, 'high');
    assert.equal(requirements.minimumEffort, 'high');
    assert.equal(requirements.independentReviewRequired, true);
    assert.throws(() => assertQualityFloor({requestedEffort: 'low', requirements}), /QUALITY_FLOOR_NOT_MET/);
  }
});

test('standard and multi-file work needs at least medium effort', () => {
  for (const complexity of ['standard', 'complex', 'multi-file']) {
    assert.equal(qualityRequirements({risk: 'medium', complexity}).minimumEffort, 'medium');
  }
});

test('each escalation trigger raises reasoning before another failed low-effort attempt', () => {
  const histories = [
    {failedAttempts: 2}, {failedAttempts: 3}, {repeatedDefect: true}, {criticalInvariantFailed: true},
    {correctnessUncertain: true}, {securityUncertain: true}, {privacyUncertain: true},
    {financialUncertain: true}, {substantiveReviewDefect: true},
  ];
  for (const history of histories) {
    const requirements = qualityRequirements({risk: 'medium', complexity: 'simple', history});
    assert.equal(requirements.minimumEffort, 'high');
    assert.ok(requirements.reasons.length);
  }
  assert.equal(qualityRequirements({risk: 'low', history: {failedAttempts: 1}}).minimumEffort, 'low');
  assert.throws(() => qualityRequirements({risk: 'low', history: {failedAttempts: -1}}), /INVALID_FAILURE_HISTORY/);
  assert.throws(() => qualityRequirements({risk: 'low', history: {financialUncertain: 'false'}}), /INVALID_FAILURE_HISTORY/);
});

test('architecture and sensitive labels cannot be relabeled as routine to lower quality', () => {
  for (const taskType of ['architecture', 'security', 'privacy', 'financial', 'tax', 'authorization', 'migration', 'release-tooling']) {
    const requirements = qualityRequirements({risk: 'low', complexity: 'simple', taskType});
    assert.equal(requirements.minimumEffort, 'high');
    if (taskType !== 'architecture') {
      assert.equal(requirements.risk, 'high');
      assert.equal(requirements.independentReviewRequired, true);
    }
  }
});

test('critical quality and owner gates are invariant under quota inputs and overrides', () => {
  for (const quota of ['healthy', 'low', 'exhausted', 'unknown']) {
    const requirements = qualityRequirements({risk: 'critical', quota, overrides: {reasoningEffort: 'low'}});
    assert.equal(requirements.minimumEffort, 'high');
    assert.ok(requirements.gates.includes('OWNER_RELEASE_APPROVAL_REQUIRED'));
    assert.ok(requirements.gates.includes('INDEPENDENT_DIFFERENT_FAMILY_REVIEW_REQUIRED'));
    assert.throws(() => assertQualityFloor({requestedEffort: 'high', effectiveEffort: 'low', requirements}), /QUALITY_FLOOR_NOT_MET/);
    assert.equal(assertQualityFloor({requestedEffort: 'high', requirements}), true);
  }
});

const baseSha = 'a'.repeat(40);
const headSha = 'b'.repeat(40);
const implementation = {provider: 'deepseek', actualModel: 'deepseek-v4-pro', baseSha, headSha};
const review = {provider: 'anthropic', actualModel: 'claude-sonnet-5-5', baseSha, headSha, outcome: 'clean', substantiveDefects: 0, participatedInImplementation: false};

test('independent review validates exact comparison and different actual family', () => {
  assert.equal(assertIndependentReview({implementation, review, headSha, baseSha}).independent, true);
  for (const actualModel of ['deepseek-v4-pro', 'deepseek-flash']) {
    assert.throws(() => assertIndependentReview({implementation, review: {...review, provider: 'deepseek', actualModel}, headSha, baseSha}), /INDEPENDENT_MODEL_REQUIRED/);
  }
  assert.throws(() => assertIndependentReview({implementation, review: {...review, headSha: 'c'.repeat(40)}, headSha, baseSha}), /STALE_REVIEW_COMPARISON/);
  assert.throws(() => assertIndependentReview({implementation: {...implementation, baseSha: 'c'.repeat(40)}, review, headSha, baseSha}), /STALE_REVIEW_COMPARISON/);
});

test('review aliases, forged family labels, unresolved authorship and findings cannot establish independence', () => {
  assert.throws(() => assertIndependentReview({implementation, review: {...review, actualModel: 'sonnet'}, headSha, baseSha}), /INVALID_MODEL_IDENTITY/);
  assert.throws(() => assertIndependentReview({implementation, review: {...review, family: 'openai'}, headSha, baseSha}), /INVALID_MODEL_IDENTITY/);
  assert.throws(() => assertIndependentReview({implementation, review: {...review, substantiveDefects: 1}, headSha, baseSha}), /CLEAN_REVIEW_REQUIRED/);
  assert.throws(() => assertIndependentReview({implementation, review: {...review, outcome: 'pending'}, headSha, baseSha}), /CLEAN_REVIEW_REQUIRED/);
  assert.throws(() => assertIndependentReview({implementation, review: {...review, participatedInImplementation: undefined}, headSha, baseSha}), /REVIEWER_AUTHORSHIP_UNRESOLVED/);
  assert.throws(() => assertIndependentReview({implementation, review, headSha}), /EXACT_COMPARISON_REQUIRED/);
});
