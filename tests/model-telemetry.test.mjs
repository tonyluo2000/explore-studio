import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, readFile, rm, symlink, mkdir, realpath} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {decisionRecord, appendDecisionRecord, aggregateUsage} from '../scripts/model-telemetry.mjs';

const route = {repository: 'tonyluo2000/mile-commons', taskType: 'routine', provider: 'openai', model: 'gpt-6-luna',
  family: 'openai', requestedEffort: 'low', effectiveEffort: 'low', risk: 'low', complexity: 'simple',
  quota: {codex: {state: 'healthy'}, claude: {state: 'unknown'}}, gates: ['PROJECT_CI_REQUIRED']};
const record = options => decisionRecord({route, taskId: 'synthetic-task', timestamp: 1000, ...options});

test('decision telemetry logs metadata and discards prompts, personal data, errors and unknown keys', () => {
  const secret = 'DO-NOT-LOG-THIS-SOURCE-OR-SECRET';
  const result = record({route: {...route, title: secret, prompt: secret, password: secret,
    reasons: [secret], gates: ['PROJECT_CI_REQUIRED', secret], reviewer: {provider: 'deepseek', model: secret}},
  execution: {status: 'failed', stderr: secret}, usage: {privateData: secret}, quality: {findingsText: secret}});
  assert.ok(!JSON.stringify(result).includes(secret));
  assert.deepEqual(result.gates, ['PROJECT_CI_REQUIRED']);
  assert.equal(result.reviewer, null);
  assert.equal(result.approvalAuthority, 'NONE');
});

test('requested identity is never claimed as actual without runtime evidence', () => {
  const planned = record();
  assert.equal(planned.requested.model, 'gpt-6-luna');
  assert.equal(planned.actual.model, null);
  for (const execution of [
    {status: 'succeeded', provider: 'openai', actualModel: 'gpt-6-luna', effectiveEffort: 'low'},
    {status: 'mock', provider: 'openai', actualModel: 'gpt-6-luna', effectiveEffort: 'low', identitySource: 'runtime_metadata'},
    {status: 'succeeded', provider: 'openai', actualModel: 'invented-model', effectiveEffort: 'low', identitySource: 'provider_response'},
  ]) assert.equal(record({execution}).actual.model, null);
  const observed = record({execution: {status: 'succeeded', provider: 'openai', actualModel: 'gpt-6-luna', effectiveEffort: 'low', identitySource: 'runtime_metadata'}});
  assert.equal(observed.actual.model, 'gpt-6-luna');
  assert.equal(observed.actual.effort, 'low');
});

test('DeepSeek medium is not recorded as effective effort', () => {
  const result = record({route: {...route, provider: 'deepseek', model: 'deepseek-v4-pro', effectiveEffort: 'medium'},
    execution: {status: 'succeeded', provider: 'deepseek', actualModel: 'deepseek-v4-pro', effectiveEffort: 'medium', identitySource: 'provider_response'}});
  assert.equal(result.selectedEffectiveEffort, null);
  assert.equal(result.actual.effort, null);
});

test('quota constraints never imply DeepSeek opt-in or an automatic backup reason', () => {
  for (const state of ['healthy', 'low', 'exhausted', 'rate_limited', 'imminent', 'unknown']) {
    const result = record({route: {...route, provider: 'deepseek', model: 'deepseek-v4-pro',
      quota: {codex: {state}}, backupReason: 'secret quota details'}});
    assert.equal(result.backupReason, null);
    assert.equal(result.ownerRequestedDeepSeek, false);
    assert.equal(result.primaryQuota.codex.state, state);
    assert.ok(!JSON.stringify(result).includes('secret quota details'));
  }
});

test('only explicit owner opt-in is recorded as the DeepSeek selection reason', () => {
  for (const explicit of [{ownerRequestedDeepSeek: true}, {backupReason: 'OWNER_EXPLICIT_REQUEST'}]) {
    const result = record({route: {...route, provider: 'deepseek', model: 'deepseek-v4-pro', ...explicit}});
    assert.equal(result.backupReason, 'OWNER_EXPLICIT_REQUEST');
    assert.equal(result.ownerRequestedDeepSeek, true);
  }
  const primary = record({route: {...route, ownerRequestedDeepSeek: true}});
  assert.equal(primary.backupActive, false);
  assert.equal(primary.backupReason, null);
  assert.equal(record({route: {...route, ownerRequestedDeepSeek: 'true'}}).ownerRequestedDeepSeek, false);
});

test('unavailable token, price, savings and outcome measurements remain unknown', () => {
  const result = record({cost: {actualUsd: 0.1}});
  assert.equal(result.usage.inputTokens, null);
  assert.equal(result.cost.actualUsd, null);
  assert.equal(result.quality.accepted, null);
  const report = aggregateUsage([result], {now: 2000});
  assert.equal(report.tokens.inputTokens.value, null);
  assert.equal(report.ciCostUsd.value, null);
  assert.equal(report.reworkRate, null);
  assert.equal(report.savings, 'NOT_MEASURED');
});

test('first-week report counts measured attempts once, while separating tasks, outcomes and costs', () => {
  const started = record({execution: {status: 'started'}, timestamp: 1000});
  const done = record({execution: {status: 'succeeded'}, timestamp: 1100, usage: {inputTokens: 10, outputTokens: 5},
    cost: {estimatedUsd: 0.01, ciUsd: 0.02}, quality: {accepted: true, delivered: true, rework: false, reviewFindings: {P1: 0}}});
  const retry = record({attempt: 2, timestamp: 1200, route: {...route, quota: {codex: {state: 'rate_limited'}}},
    execution: {status: 'failed'}, usage: {inputTokens: 3, outputTokens: 1}, quality: {accepted: false, delivered: false, rework: true}});
  const second = record({taskId: 'another-task', timestamp: 1500, route: {...route, provider: 'deepseek', model: 'deepseek-v4-pro', ownerRequestedDeepSeek: true, quota: {codex: {state: 'exhausted'}}},
    execution: {status: 'succeeded', provider: 'deepseek', actualModel: 'deepseek-v4-pro', effectiveEffort: 'low', identitySource: 'provider_response'},
    usage: {inputTokens: 2, outputTokens: 4}, cost: {actualUsd: 0.004, actualSource: 'provider_response'},
    quality: {accepted: true, delivered: true, rework: false, reviewFindings: {P1: 1}}});
  const report = aggregateUsage([started, done, retry, second], {now: 2000});
  assert.equal(report.eventCount, 4);
  assert.equal(report.taskCount, 2);
  assert.equal(report.attemptCount, 3);
  assert.equal(report.tokens.inputTokens.value, 15);
  assert.equal(report.deepseekActualCostUsd.value, 0.004);
  assert.equal(report.ciCostUsd.value, 0.02);
  assert.equal(report.quotaInterruptions.codex, 2);
  assert.equal(report.acceptedTasks, 1);
  assert.equal(report.deliveredTasks, 1);
  assert.equal(report.reworkRate, 0.5);
  assert.equal(Object.values(report.selections).reduce((a, b) => a + b, 0), 3);
});

test('report excludes future and out-of-window records', () => {
  const report = aggregateUsage([record({timestamp: 100}), record({timestamp: 1000}), record({timestamp: 2100})], {now: 2000, windowMs: 1500});
  assert.equal(report.eventCount, 1);
  assert.throws(() => aggregateUsage([], {windowMs: 0}), /INVALID_REPORT_WINDOW/);
});

test('ledger append revalidates metadata, excludes extra secrets and refuses symlinks', async t => {
  const directory = await realpath(await mkdtemp(path.join(os.tmpdir(), 'model-telemetry-')));
  t.after(() => rm(directory, {recursive: true, force: true}));
  const filename = path.join(directory, 'ledger.jsonl');
  await appendDecisionRecord(filename, {...record(), secret: 'NEVER-PERSIST-ME'});
  const saved = await readFile(filename, 'utf8');
  assert.ok(!saved.includes('NEVER-PERSIST-ME'));
  assert.equal(JSON.parse(saved).schema, 'cross-project.model-decision.v1');
  await appendDecisionRecord(filename, record({route: {...route, provider: 'deepseek', model: 'deepseek-v4-pro', ownerRequestedDeepSeek: true}}));
  const optedIn = JSON.parse((await readFile(filename, 'utf8')).trim().split('\n').at(-1));
  assert.equal(optedIn.ownerRequestedDeepSeek, true);
  assert.equal(optedIn.backupReason, 'OWNER_EXPLICIT_REQUEST');
  const linked = path.join(directory, 'linked.jsonl');
  await symlink(filename, linked);
  await assert.rejects(appendDecisionRecord(linked, record()));
  await mkdir(path.join(directory, 'real'));
  await symlink(path.join(directory, 'real'), path.join(directory, 'alias'));
  await assert.rejects(appendDecisionRecord(path.join(directory, 'alias', 'ledger'), record()), /TELEMETRY_UNSAFE_PATH/);
});
