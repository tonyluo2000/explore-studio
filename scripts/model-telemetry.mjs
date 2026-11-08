#!/usr/bin/env node
import {constants} from 'node:fs';
import {open, lstat, readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {MODEL_CATALOG} from './model-capabilities.mjs';

const SCHEMA = 'cross-project.model-decision.v1';
const PROJECTS = new Set(['tonyluo2000/mile-commons', 'briersystems/montefinance', 'tonyluo2000/explore-studio']);
const EFFORTS = new Set(['low', 'medium', 'high']);
const QUOTAS = new Set(['unknown', 'healthy', 'low', 'exhausted', 'rate_limited', 'imminent']);
const TASKS = new Set(['routine', 'documentation', 'formatting', 'simple-tests', 'implementation', 'feature', 'bugfix', 'integration', 'review', 'security', 'architecture', 'debugging', 'privacy', 'financial', 'tax', 'authorization', 'migration', 'release-tooling', 'release']);
const STATUSES = new Set(['planned', 'mock', 'started', 'succeeded', 'failed', 'blocked']);
const MEASUREMENT_SOURCES = new Set(['provider_response', 'runtime_metadata']);
const REASONS = new Set(['UNKNOWN_RISK', 'HIGH_RISK', 'ARCHITECTURE', 'TWO_FAILED_ATTEMPTS', 'REPEATED_DEFECT', 'CRITICAL_INVARIANT_FAILED', 'CORRECTNESS_UNCERTAIN', 'SECURITY_UNCERTAIN', 'PRIVACY_UNCERTAIN', 'FINANCIAL_UNCERTAIN', 'SUBSTANTIVE_REVIEW_DEFECT']);
const GATES = new Set(['PROJECT_CI_REQUIRED', 'PROJECT_SECURITY_GATES_REQUIRED', 'EXACT_HEAD_REVIEW_REQUIRED', 'INDEPENDENT_DIFFERENT_FAMILY_REVIEW_REQUIRED', 'OWNER_RELEASE_APPROVAL_REQUIRED', 'EXTERNAL_TRANSFER_AUTHORIZATION_REQUIRED', 'PAID_CALL_AUTHORIZATION_REQUIRED', 'SPENDING_LIMIT_REQUIRED', 'INDEPENDENT_SECURITY_REVIEW_REQUIRED', 'REVIEWED_ACTIVATION_REQUIRED']);
const fail = code => { throw Object.assign(new Error(code), {code}); };
const count = value => Number.isSafeInteger(value) && value >= 0 ? value : null;
const money = value => Number.isFinite(value) && value >= 0 ? value : null;
const bool = value => typeof value === 'boolean' ? value : null;
const oneOf = (value, choices) => choices.has(value) ? value : null;
const enumArray = (values, choices) => [...new Set((Array.isArray(values) ? values : []).filter(value => choices.has(value)))];
const identity = (provider, model) => MODEL_CATALOG.find(entry => entry.provider === provider && entry.model === model);

// Deliberately construct every output field. Never spread task text, errors,
// provider responses, source paths or arbitrary object properties into a log.
export function decisionRecord({route, taskId, attempt = 1, timestamp = Date.now(), execution = {}, usage = {}, cost = {}, quality = {}}) {
  const repository = route?.repository;
  if (!PROJECTS.has(repository) || !/^[a-z0-9][a-z0-9-]{0,63}$/.test(taskId ?? '')
    || !Number.isSafeInteger(attempt) || attempt < 1 || !Number.isFinite(timestamp) || timestamp < 0) fail('INVALID_DECISION_IDENTITY');
  const requested = identity(route.provider, route.model);
  const status = oneOf(execution.status, STATUSES) ?? 'planned';
  const observed = identity(execution.provider, execution.actualModel);
  const actualVerified = !['planned', 'mock', 'blocked'].includes(status)
    && MEASUREMENT_SOURCES.has(execution.identitySource) && !!observed;
  const effectiveEffort = actualVerified && observed.efforts.includes(execution.effectiveEffort) ? execution.effectiveEffort : null;
  const primaryQuota = Object.fromEntries(['codex', 'claude'].map(provider => {
    const quota = route.quota?.[provider] ?? route.primaryQuota?.[provider];
    return [provider, {state: oneOf(typeof quota === 'string' ? quota : quota?.state, QUOTAS) ?? 'unknown'}];
  }));
  const backupActive = requested?.provider === 'deepseek';
  const role = oneOf(route.role, new Set(['implementation', 'review'])) ?? (route.taskType === 'review' ? 'review' : 'implementation');
  const primaryRole = oneOf(route.primaryRole, new Set(['codex', 'claude'])) ?? (role === 'review' ? 'claude' : 'codex');
  // A quota observation is telemetry only. The owner must explicitly request
  // DeepSeek Pro for this task; low or exhausted quotas never imply opt-in.
  const ownerRequestedDeepSeek = route.ownerRequestedDeepSeek === true || route.backupReason === 'EXPLICIT_OWNER_REQUEST';
  const backupReason = backupActive && ownerRequestedDeepSeek ? 'EXPLICIT_OWNER_REQUEST' : null;
  const ownerAuthorizationId = backupActive && /^[a-z0-9][a-z0-9-]{7,95}$/.test(route.ownerAuthorizationId ?? '') ? route.ownerAuthorizationId : null;
  const reviewerIdentity = route.reviewer && identity(route.reviewer.provider, route.reviewer.model);
  return {
    schema: SCHEMA, timestamp, repository, taskId, attempt,
    taskType: oneOf(route.taskType, TASKS), role, primaryRole,
    complexity: oneOf(route.complexity, new Set(['routine', 'simple', 'standard', 'complex', 'multi-file', 'architecture', 'difficult', 'difficult-debugging'])) ?? 'unknown',
    risk: oneOf(route.risk, new Set(['low', 'medium', 'high', 'critical'])) ?? 'high',
    requested: {provider: requested?.provider ?? null, model: requested?.model ?? null,
      effort: oneOf(route.requestedEffort ?? route.reasoningEffort, EFFORTS)},
    selectedEffectiveEffort: requested?.efforts.includes(route.effectiveEffort ?? route.reasoningEffort) ? route.effectiveEffort ?? route.reasoningEffort : null,
    actual: {provider: actualVerified ? observed.provider : null, model: actualVerified ? observed.model : null,
      effort: effectiveEffort, identitySource: actualVerified ? execution.identitySource : null},
    primaryQuota, backupActive, backupReason, ownerRequestedDeepSeek, ownerAuthorizationId,
    selectionAvailability: oneOf(route.availability, new Set(['verified','unknown'])) ?? 'unknown',
    reviewBlocked: bool(route.reviewBlocked),
    reviewer: reviewerIdentity ? {provider: reviewerIdentity.provider, model: reviewerIdentity.model} : null,
    gates: enumArray(route.gates, GATES), reasons: enumArray(route.reasons, REASONS),
    execution: {status, durationMs: count(execution.durationMs), exitCode: count(execution.exitCode)},
    usage: {inputTokens: count(usage.inputTokens), outputTokens: count(usage.outputTokens),
      reasoningTokens: count(usage.reasoningTokens), cachedInputTokens: count(usage.cachedInputTokens)},
    cost: {estimatedUsd: money(cost.estimatedUsd),
      actualUsd: ['provider_response', 'invoice'].includes(cost.actualSource) ? money(cost.actualUsd) : null,
      actualSource: ['provider_response', 'invoice'].includes(cost.actualSource) ? cost.actualSource : null,
      ciUsd: money(cost.ciUsd)},
    quality: {testsPassed: count(quality.testsPassed), testsFailed: count(quality.testsFailed), testsSkipped: count(quality.testsSkipped),
      accepted: bool(quality.accepted), delivered: bool(quality.delivered), rework: bool(quality.rework),
      reviewFindings: Object.fromEntries(['P0', 'P1', 'P2', 'P3'].map(priority => [priority, count(quality.reviewFindings?.[priority])]))},
    savings: 'NOT_MEASURED', approvalAuthority: 'NONE',
  };
}

function sanitizeRecord(record) {
  if (record?.schema !== SCHEMA) fail('INVALID_DECISION_RECORD');
  return decisionRecord({
    taskId: record.taskId, attempt: record.attempt, timestamp: record.timestamp,
    route: {repository: record.repository, taskType: record.taskType, role: record.role, primaryRole: record.primaryRole, risk: record.risk, complexity: record.complexity,
      provider: record.requested?.provider, model: record.requested?.model, requestedEffort: record.requested?.effort,
      effectiveEffort: record.selectedEffectiveEffort, quota: record.primaryQuota, reviewer: record.reviewer,
      gates: record.gates, reasons: record.reasons, ownerRequestedDeepSeek: record.ownerRequestedDeepSeek,
      backupReason: record.backupReason, ownerAuthorizationId: record.ownerAuthorizationId,
      availability: record.selectionAvailability, reviewBlocked: record.reviewBlocked},
    execution: {...record.execution, provider: record.actual?.provider, actualModel: record.actual?.model,
      effectiveEffort: record.actual?.effort, identitySource: record.actual?.identitySource},
    usage: record.usage, cost: record.cost, quality: record.quality,
  });
}

export async function appendDecisionRecord(filename, record) {
  const safeRecord = sanitizeRecord(record);
  const resolved = path.resolve(filename);
  // Refuse symlink parents and destinations. The operator creates the ledger's
  // directory; this function does not create or change global configuration.
  const parsed = path.parse(resolved);
  let current = parsed.root;
  for (const component of path.dirname(resolved).slice(parsed.root.length).split(path.sep).filter(Boolean)) {
    current = path.join(current, component);
    const stat = await lstat(current);
    if (!stat.isDirectory() || stat.isSymbolicLink()) fail('TELEMETRY_UNSAFE_PATH');
  }
  const serialized = `${JSON.stringify(safeRecord)}\n`;
  if (Buffer.byteLength(serialized) > 16_000) fail('DECISION_RECORD_TOO_LARGE');
  const handle = await open(resolved, constants.O_WRONLY | constants.O_APPEND | constants.O_CREAT | constants.O_NOFOLLOW, 0o600);
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.nlink !== 1 || stat.size > 8_000_000) fail('TELEMETRY_UNSAFE_FILE');
    await handle.writeFile(serialized);
    await handle.sync();
  } finally { await handle.close(); }
  return safeRecord;
}

function measuredSum(records, select) {
  const measurements = records.map(select).filter(value => value !== null && value !== undefined);
  return {value: measurements.length ? measurements.reduce((total, value) => total + value, 0) : null, measuredRecords: measurements.length};
}

export function aggregateUsage(records, {now = Date.now(), windowMs = 7 * 24 * 60 * 60 * 1000} = {}) {
  if (!Array.isArray(records) || !Number.isFinite(now) || !Number.isFinite(windowMs) || windowMs <= 0) fail('INVALID_REPORT_WINDOW');
  const recent = records.filter(record => record?.schema === SCHEMA && Number.isFinite(record.timestamp)
    && record.timestamp <= now && record.timestamp > now - windowMs).map(sanitizeRecord);
  // A task may have planned, started and result events. Use the latest event
  // per project/task for outcomes and token/cost totals to prevent double-counts.
  const tasks = new Map();
  const attempts = new Map();
  for (const record of [...recent].sort((a, b) => a.timestamp - b.timestamp)) {
    tasks.set(`${record.repository}:${record.taskId}`, record);
    attempts.set(`${record.repository}:${record.taskId}:${record.attempt}`, record);
  }
  const latest = [...tasks.values()];
  const executions = [...attempts.values()];
  const selections = {};
  for (const record of executions) {
    const key = `${record.repository}:${record.requested?.provider ?? 'unknown'}:${record.requested?.model ?? 'unknown'}:${record.requested?.effort ?? 'unknown'}`;
    selections[key] = (selections[key] ?? 0) + 1;
  }
  const dispositions = latest.filter(record => typeof record.quality?.accepted === 'boolean');
  const reworkMeasured = dispositions.filter(record => typeof record.quality?.rework === 'boolean');
  const deepseek = executions.filter(record => record.actual?.provider === 'deepseek');
  return {
    windowStart: now - windowMs, windowEnd: now, eventCount: recent.length, taskCount: latest.length, attemptCount: executions.length,
    selections,
    quotaInterruptions: Object.fromEntries(['codex', 'claude'].map(provider => [provider,
      executions.filter(record => ['exhausted', 'rate_limited'].includes(record.primaryQuota?.[provider]?.state)).length])),
    tokens: Object.fromEntries(['inputTokens', 'outputTokens', 'reasoningTokens', 'cachedInputTokens'].map(key => [key, measuredSum(executions, record => record.usage?.[key])])),
    deepseekActualCostUsd: measuredSum(deepseek, record => record.cost?.actualUsd),
    estimatedCostUsd: measuredSum(executions, record => record.cost?.estimatedUsd),
    ciCostUsd: measuredSum(executions, record => record.cost?.ciUsd),
    acceptedTasks: dispositions.filter(record => record.quality.accepted).length,
    acceptedMeasuredTasks: dispositions.length,
    deliveredTasks: latest.filter(record => record.quality?.delivered === true).length,
    deliveredMeasuredTasks: latest.filter(record => typeof record.quality?.delivered === 'boolean').length,
    reworkTasks: reworkMeasured.filter(record => record.quality.rework).length,
    reworkMeasuredTasks: reworkMeasured.length,
    reworkRate: reworkMeasured.length ? reworkMeasured.filter(record => record.quality.rework).length / reworkMeasured.length : null,
    reviewFindings: Object.fromEntries(['P0', 'P1', 'P2', 'P3'].map(priority => [priority, measuredSum(latest, record => record.quality?.reviewFindings?.[priority])])),
    savings: 'NOT_MEASURED',
  };
}

async function main(argv) {
  if (argv.length !== 2 || argv[0] !== 'report') fail('usage: model-telemetry.mjs report LEDGER.jsonl');
  const stat = await lstat(argv[1]);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 8_000_000) fail('TELEMETRY_UNSAFE_FILE');
  const records = (await readFile(argv[1], 'utf8')).split('\n').filter(Boolean).map(line => JSON.parse(line));
  console.log(JSON.stringify(aggregateUsage(records), null, 2));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch(error => { console.error(error.code ?? 'TELEMETRY_REPORT_FAILED'); process.exitCode = 1; });
}
