import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { mkdir, lstat, open, readdir, readFile, rmdir } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

export const REQUEST_CAP_USD = 1;
export const SHARED_CAP_USD = 10;
// Disjoint fixed pools keep all three local adapters plus the hosted gateway
// within the existing global ceiling without adding a cross-host service.
export const LOCAL_CAP_USD = 5;
export const HOSTED_CAP_USD = 5;
export const WINDOW_MS = 7 * 24 * 60 * 60 * 1000;
export const DEFAULT_LEDGER_DIRECTORY = path.join(os.homedir(), '.local', 'state', 'deepseek-workflow');
const REPOSITORIES = new Set(['tonyluo2000/mile-commons', 'briersystems/montefinance', 'tonyluo2000/explore-studio']);
const fail = (code) => { throw Object.assign(new Error(code), { code }); };
const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const micros = value => Math.ceil(value * 1_000_000);

async function safeDirectory(directory) {
  const resolved = path.resolve(directory);
  for (let current = path.parse(resolved).root, parts = resolved.slice(current.length).split(path.sep), i = 0; i < parts.length; i++) {
    current = path.join(current, parts[i]);
    try { await mkdir(current, { mode: 0o700 }); } catch (error) { if (error.code !== 'EEXIST') throw error; }
    const stat = await lstat(current);
    if (!stat.isDirectory() || stat.isSymbolicLink()) fail('LEDGER_UNSAFE_PATH');
  }
  const owner = await lstat(resolved);
  if ((owner.mode & 0o777) !== 0o700 || typeof process.geteuid === 'function' && owner.uid !== process.geteuid()) fail('LEDGER_PERMISSIONS_INVALID');
  return resolved;
}

function validateIdentity(identity) {
  if (!identity || !REPOSITORIES.has(identity.repository) || identity.provider !== 'deepseek'
    || identity.actualModel !== 'deepseek-v4-pro'
    || !['review', 'implementation'].includes(identity.taskType)
    || !/^[a-z0-9][a-z0-9-]{0,63}$/.test(identity.taskId ?? '')
    || !/^[a-z0-9][a-z0-9-]{7,95}$/.test(identity.authorizationId ?? '')
    || !['low', 'high'].includes(identity.reasoningEffort)
    || !/^[a-f0-9]{40}$/.test(identity.baseSha ?? '')
    || !/^[a-f0-9]{40}$/.test(identity.headSha ?? '')
    || !/^[a-f0-9]{64}$/.test(identity.requestId ?? '')) fail('LEDGER_IDENTITY_INVALID');
  // actualModel is the legacy expected-model identity of a reservation. Only
  // the result's resolvedModel records the provider-attested model.
  const result = Object.fromEntries(['repository', 'provider', 'actualModel', 'taskType', 'taskId', 'authorizationId', 'reasoningEffort', 'requestId'].map(key => [key, identity[key]]));
  for (const key of ['baseSha', 'headSha']) {
    if (identity[key] !== undefined) {
      if (!/^[a-f0-9]{40}$/.test(identity[key])) fail('LEDGER_IDENTITY_INVALID');
      result[key] = identity[key];
    }
  }
  if (identity.pullNumber !== undefined) {
    if (!Number.isSafeInteger(identity.pullNumber) || identity.pullNumber < 1) fail('LEDGER_IDENTITY_INVALID');
    result.pullNumber = identity.pullNumber;
  }
  return result;
}

async function entries(directory) {
  const names = (await readdir(directory)).filter(name => name !== 'active.lock').sort();
  let previous = null;
  const result = [];
  for (const [index, name] of names.entries()) {
    if (name !== `${String(index + 1).padStart(10, '0')}.json`) fail('LEDGER_CORRUPT');
    const file = path.join(directory, name);
    const stat = await lstat(file);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 64_000) fail('LEDGER_CORRUPT');
    const event = JSON.parse(await readFile(file, 'utf8'));
    const { hash, ...body } = event;
    if (hash !== digest(body) || body.previous !== previous || !Number.isFinite(body.timestamp)) fail('LEDGER_CORRUPT');
    if (body.type === 'reservation' && (!Number.isSafeInteger(body.reservedMicros) || body.reservedMicros < 1 || body.reservedMicros > 1_000_000)) fail('LEDGER_CORRUPT');
    result.push(event);
    previous = hash;
  }
  return result;
}

async function append(directory, history, body) {
  const event = { ...body, previous: history.at(-1)?.hash ?? null };
  event.hash = digest(event);
  const file = path.join(directory, `${String(history.length + 1).padStart(10, '0')}.json`);
  const handle = await open(file, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, 0o600);
  try { await handle.writeFile(`${JSON.stringify(event)}\n`); await handle.sync(); await handle.chmod(0o400); } finally { await handle.close(); }
  history.push(event);
  return event;
}

function usageOf(result) {
  const usage = result?.usage;
  if (!usage) return null;
  const keys = ['prompt_tokens', 'completion_tokens', 'total_tokens', 'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens'];
  return Object.fromEntries(keys.filter(key => Number.isSafeInteger(usage[key]) && usage[key] >= 0).map(key => [key, usage[key]]));
}

// The lock is held across the provider request. Never automatically steal a
// stale lock: process death could mean a paid request is still in flight.
export async function withBudget({ identity, maximumCostUsd, ledgerDirectory = DEFAULT_LEDGER_DIRECTORY }, callback) {
  const safeIdentity = validateIdentity(identity);
  if (process.env.GITHUB_ACTIONS === 'true') {
    let hosted;
    try { hosted = await import('./deepseek-hosted-budget.mjs'); }
    catch { fail('SHARED_LEDGER_UNAVAILABLE'); }
    if (typeof hosted.withHostedBudget !== 'function') fail('SHARED_LEDGER_UNAVAILABLE');
    return hosted.withHostedBudget({identity,maximumCostUsd},callback);
  }
  // Hosted run identities cannot be replayed against the separate local pool.
  if (safeIdentity.authorizationId.startsWith('gh-run-')) fail('HOSTED_ID_ON_LOCAL_LEDGER');
  if (!Number.isFinite(maximumCostUsd) || maximumCostUsd <= 0 || maximumCostUsd > REQUEST_CAP_USD) fail('REQUEST_CAP_EXCEEDED');
  const directory = await safeDirectory(ledgerDirectory);
  const lock = path.join(directory, 'active.lock');
  try { await mkdir(lock, { mode: 0o700 }); } catch (error) { if (error.code === 'EEXIST') fail('PAID_REQUEST_ALREADY_ACTIVE'); throw error; }
  try {
    const history = await entries(directory);
    const timestamp = Date.now();
    const reservations = history.filter(event => event.type === 'reservation');
    if (reservations.some(event => event.identity.requestId === safeIdentity.requestId)) fail('PAID_REQUEST_REPLAY_DENIED');
    // An owner request authorizes one call, not a reusable provider preference.
    // Retain this check across the entire ledger, including expired windows.
    if (reservations.some(event => event.identity.authorizationId === safeIdentity.authorizationId)) fail('PAID_AUTHORIZATION_REPLAY_DENIED');
    if (history.some(event => event.timestamp > timestamp)) fail('LEDGER_CLOCK_ROLLBACK');
    const reservedMicros = micros(maximumCostUsd);
    const used = reservations.filter(event => event.timestamp >= timestamp - WINDOW_MS).reduce((sum, event) => sum + event.reservedMicros, 0);
    if (used + reservedMicros > micros(LOCAL_CAP_USD)) fail('SHARED_WEEKLY_CAP_EXCEEDED');
    await append(directory, history, { type: 'reservation', timestamp, identity: safeIdentity, reservedMicros });
    const started = Date.now();
    let result;
    try {
      result = await callback();
    } catch (error) {
      // The fixed transport can attest identity/usage even when its content is
      // truncated or fails schema validation. Keep that accounting without
      // storing the raw response or treating the task as a completed review.
      const receipt = error?.providerReceipt;
      const usage = receipt?.usage;
      const attested = receipt?.schema === 'cross-project.deepseek-provider-receipt.v1'
        && receipt.resolvedModel === safeIdentity.actualModel && receipt.reasoningEffort === safeIdentity.reasoningEffort
        && ['prompt_tokens','completion_tokens','total_tokens'].every(key=>Number.isSafeInteger(usage?.[key]) && usage[key]>=0)
        && usage.total_tokens === usage.prompt_tokens + usage.completion_tokens;
      const knownUsage = attested ? usageOf(receipt) : null;
      await append(directory, history, { type: 'result', timestamp: Date.now(), requestId: safeIdentity.requestId, status: 'FAILED_OR_AMBIGUOUS', resolvedModel: knownUsage ? receipt.resolvedModel : null, durationMs: Date.now() - started, accepted: null, rework: null, usage: knownUsage, reportedCostUsd: null });
      throw error;
    }
    const rates = safeIdentity.actualModel === 'deepseek-v4-pro' ? { input: 1.32, output: 3.96 } : { input: 0.3, output: 1.2 };
    const usage = usageOf(result);
    const estimatedCostUpperBoundUsd = usage?.prompt_tokens !== undefined && usage?.completion_tokens !== undefined
      ? (usage.prompt_tokens * rates.input + usage.completion_tokens * rates.output) / 1_000_000 : null;
    await append(directory, history, { type: 'result', timestamp: Date.now(), requestId: safeIdentity.requestId, status: 'PROVIDER_RETURNED', resolvedModel: result?.resolvedModel ?? null, durationMs: Date.now() - started, accepted: null, rework: null, usage, estimatedCostUpperBoundUsd, reportedCostUsd: null });
    return result;
  } finally { await rmdir(lock); }
}

export async function recordOutcome({ requestId, accepted, rework, findingCounts, ledgerDirectory = DEFAULT_LEDGER_DIRECTORY }) {
  if (!/^[a-f0-9]{64}$/.test(requestId ?? '') || typeof accepted !== 'boolean' || typeof rework !== 'boolean'
    || !findingCounts || Object.keys(findingCounts).some(key => !['P0', 'P1', 'P2', 'P3'].includes(key))
    || Object.values(findingCounts).some(count => !Number.isSafeInteger(count) || count < 0)) fail('LEDGER_OUTCOME_INVALID');
  const directory = await safeDirectory(ledgerDirectory);
  const lock = path.join(directory, 'active.lock');
  try { await mkdir(lock, { mode: 0o700 }); } catch (error) { if (error.code === 'EEXIST') fail('PAID_REQUEST_ALREADY_ACTIVE'); throw error; }
  try {
    const history = await entries(directory);
    if (!history.some(event => event.type === 'result' && event.requestId === requestId)) fail('LEDGER_REQUEST_NOT_FOUND');
    return await append(directory, history, { type: 'outcome', timestamp: Date.now(), requestId, accepted, rework, findingCounts });
  } finally { await rmdir(lock); }
}

export async function budgetReport({ ledgerDirectory = DEFAULT_LEDGER_DIRECTORY, now = Date.now() } = {}) {
  const directory = await safeDirectory(ledgerDirectory);
  const history = await entries(directory);
  const recent = history.filter(event => event.timestamp >= now - WINDOW_MS);
  const reservations = recent.filter(event => event.type === 'reservation');
  const results = recent.filter(event => event.type === 'result');
  return { window: 'rolling 168 hours (stricter than calendar-week reset)', requestCapUsd: REQUEST_CAP_USD, sharedCapUsd: SHARED_CAP_USD, localCapUsd: LOCAL_CAP_USD, hostedCapUsd: HOSTED_CAP_USD, budgetScope: 'fixed disjoint local/hosted pools; unknown hosted usage is never reported as zero', hostedReservedUsd: null, reservedUsd: reservations.reduce((sum, event) => sum + event.reservedMicros, 0) / 1_000_000, requests: reservations.length, results: results.length, providerTokens: results.reduce((sum, event) => sum + (event.usage?.total_tokens ?? 0), 0), reportedCostUsd: null, reservations, outcomes: results, dispositions: recent.filter(event => event.type === 'outcome'), savings: 'NOT_MEASURED' };
}
