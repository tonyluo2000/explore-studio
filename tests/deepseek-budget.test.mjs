import test from 'node:test';
import assert from 'node:assert/strict';
import { chmod, mkdtemp, realpath, rm, writeFile, symlink } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { withBudget, budgetReport, recordOutcome } from '../scripts/deepseek-budget.mjs';
const identity = (id, repository = 'tonyluo2000/mile-commons') => ({ repository, provider: 'deepseek', actualModel: 'deepseek-v4-pro', taskType: 'review', taskId: 'synthetic-review', authorizationId: 'owner-call-' + id, reasoningEffort: 'high', baseSha: 'a'.repeat(40), headSha: 'b'.repeat(40), requestId: id.toString(16).padStart(64, '0') });
async function fixture(t) { const dir = await realpath(await mkdtemp(path.join(os.tmpdir(), 'deepseek-budget-'))); t.after(() => rm(dir, { recursive: true, force: true })); return dir; }
test('shared cap covers three projects, retains reservations and refuses replay', async t => {
  const dir = await fixture(t);
  const repos = ['tonyluo2000/mile-commons', 'briersystems/montefinance', 'tonyluo2000/explore-studio'];
  for (let i = 1; i <= 10; i++) await withBudget({ identity: identity(i, repos[i % 3]), maximumCostUsd: 1, ledgerDirectory: dir }, async () => ({ usage: { prompt_tokens: 1, completion_tokens: 2, total_tokens: 3 } }));
  await assert.rejects(withBudget({ identity: identity(11), maximumCostUsd: 0.01, ledgerDirectory: dir }, () => assert.fail('must not send')), { code: 'SHARED_WEEKLY_CAP_EXCEEDED' });
  await assert.rejects(withBudget({ identity: identity(1), maximumCostUsd: 1, ledgerDirectory: dir }, () => assert.fail()), { code: 'PAID_REQUEST_REPLAY_DENIED' });
  assert.equal((await budgetReport({ ledgerDirectory: dir })).reservedUsd, 10);
});
test('one paid request at a time and ambiguous failure never refunds', async t => {
  const dir = await fixture(t);
  await assert.rejects(withBudget({ identity: identity(1), maximumCostUsd: 1, ledgerDirectory: dir }, async () => {
    await assert.rejects(withBudget({ identity: identity(2), maximumCostUsd: 1, ledgerDirectory: dir }, () => assert.fail()), { code: 'PAID_REQUEST_ALREADY_ACTIVE' });
    throw new Error('timeout');
  }), /timeout/);
  assert.equal((await budgetReport({ ledgerDirectory: dir })).reservedUsd, 1);
  await assert.rejects(withBudget({ identity: identity(1), maximumCostUsd: 1, ledgerDirectory: dir }, () => assert.fail()), { code: 'PAID_REQUEST_REPLAY_DENIED' });
});
test('rejects bad caps, model attribution, symlinks and corrupt receipts before callback', async t => {
  const dir = await fixture(t);
  for (const amount of [NaN, 0, -1, 1.01]) await assert.rejects(withBudget({ identity: identity(1), maximumCostUsd: amount, ledgerDirectory: dir }, () => assert.fail()), { code: 'REQUEST_CAP_EXCEEDED' });
  await assert.rejects(withBudget({ identity: { ...identity(1), actualModel: 'claude-sonnet' }, maximumCostUsd: 1, ledgerDirectory: dir }, () => assert.fail()), { code: 'LEDGER_IDENTITY_INVALID' });
  const link = path.join(dir, 'link'); await symlink(dir, link);
  await assert.rejects(withBudget({ identity: identity(1), maximumCostUsd: 1, ledgerDirectory: link }, () => assert.fail()), { code: 'LEDGER_UNSAFE_PATH' });
  await rm(link);
  await writeFile(path.join(dir, '0000000001.json'), '{}');
  await assert.rejects(withBudget({ identity: identity(1), maximumCostUsd: 1, ledgerDirectory: dir }, () => assert.fail()), { code: 'LEDGER_CORRUPT' });
});
test('records usage and acceptance separately from reservation without claiming a billed charge', async t => {
  const dir = await fixture(t);
  await withBudget({ identity: identity(1), maximumCostUsd: 0.02, ledgerDirectory: dir }, async () => ({ resolvedModel: 'deepseek-v4-pro', usage: { prompt_tokens: 100, completion_tokens: 20, total_tokens: 120, prompt_cache_hit_tokens: 10, prompt_cache_miss_tokens: 90 } }));
  await recordOutcome({ requestId: identity(1).requestId, accepted: false, rework: true, findingCounts: { P1: 1 }, ledgerDirectory: dir });
  const report = await budgetReport({ ledgerDirectory: dir });
  assert.equal(report.providerTokens, 120);
  assert.equal(report.outcomes[0].usage.prompt_cache_hit_tokens, 10);
  assert.equal(report.outcomes[0].resolvedModel, 'deepseek-v4-pro');
  assert.equal(report.reportedCostUsd, null);
  assert.equal(report.reservedUsd, 0.02);
});
test('shared ledger must remain private to the current OS user', async t => {
  const dir = await fixture(t);
  await chmod(dir, 0o755);
  await assert.rejects(withBudget({ identity: identity(1), maximumCostUsd: 0.02, ledgerDirectory: dir }, () => assert.fail()), { code: 'LEDGER_PERMISSIONS_INVALID' });
  await chmod(dir, 0o700);
});

test('one owner authorization cannot reserve a different body or another project', async t => {
  const dir = await fixture(t); let calls = 0;
  await withBudget({identity: identity(20), maximumCostUsd: 0.02, ledgerDirectory: dir}, async () => {calls++; return {};});
  for (const repository of ['tonyluo2000/mile-commons', 'briersystems/montefinance']) {
    await assert.rejects(withBudget({identity: {...identity(21, repository), authorizationId: identity(20).authorizationId}, maximumCostUsd: 0.02, ledgerDirectory: dir}, () => {calls++;}), {code:'PAID_AUTHORIZATION_REPLAY_DENIED'});
  }
  assert.equal(calls,1); assert.equal((await budgetReport({ledgerDirectory:dir})).reservedUsd,0.02);
});
test('missing task-scoped authorization identity fails before ledger reservation', async t => {
  const dir = await fixture(t); let calls = 0;
  for (const field of ['taskId','authorizationId','baseSha','headSha','reasoningEffort']) {
    const value={...identity(30)}; delete value[field];
    await assert.rejects(withBudget({identity:value,maximumCostUsd:0.02,ledgerDirectory:dir},()=>{calls++;}),{code:'LEDGER_IDENTITY_INVALID'});
  }
  assert.equal(calls,0); assert.equal((await budgetReport({ledgerDirectory:dir})).requests,0);
});

test('incomplete provider content retains already-attested usage without refund or verdict',async t=>{
 const dir=await fixture(t);const usage={prompt_tokens:10,completion_tokens:8,total_tokens:18};
 await assert.rejects(withBudget({identity:identity(40),maximumCostUsd:0.02,ledgerDirectory:dir},async()=>{throw Object.assign(new Error('incomplete'),{code:'API_INCOMPLETE_RESPONSE',providerReceipt:{schema:'cross-project.deepseek-provider-receipt.v1',resolvedModel:'deepseek-v4-pro',reasoningEffort:'high',usage},raw:'never store this'});}),{code:'API_INCOMPLETE_RESPONSE'});
 const report=await budgetReport({ledgerDirectory:dir});assert.equal(report.reservedUsd,0.02);assert.equal(report.providerTokens,18);assert.equal(report.outcomes[0].status,'FAILED_OR_AMBIGUOUS');assert.equal(report.outcomes[0].resolvedModel,'deepseek-v4-pro');assert.ok(!JSON.stringify(report).includes('never store this'));
});
