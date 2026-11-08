import {constants} from 'node:fs';
import {open, realpath, lstat} from 'node:fs/promises';
import path from 'node:path';

export const HOSTED_CAP_USD = 5;
export const HOSTED_REQUEST_CAP_USD = 0.50;
const WINDOW_MS = 168 * 60 * 60 * 1000;
const MAX_DISPATCH_AGE_MS = 30 * 60 * 1000;
const JOB_TIMEOUT_MS = 10 * 60 * 1000;
const CONTROL = 'tonyluo2000/mile-commons';
const WORKFLOW = '.github/workflows/deepseek-review.yml';
// One-time reconciliation from existing owner-controlled immutable receipts.
// Full approved ceilings are retained, including ambiguous provider failures.
// Any later rerun reserves an additional full $1; missing evidence stays $1.
const LEGACY_RESERVATIONS = Object.freeze({
  '42234278868': Object.freeze({attempts:1,usd:0.02}),
  '42232247157': Object.freeze({attempts:1,usd:0}),
  '42232024359': Object.freeze({attempts:1,usd:0}),
  '42232021122': Object.freeze({attempts:1,usd:0}),
  '42229980222': Object.freeze({attempts:1,usd:0.02}),
  '41349386201': Object.freeze({attempts:1,usd:0.1}),
  '41349149423': Object.freeze({attempts:1,usd:0.1}),
  '41349145350': Object.freeze({attempts:1,usd:0.25}),
  '41344796685': Object.freeze({attempts:1,usd:0.1}),
  '41342720311': Object.freeze({attempts:1,usd:0.25}),
  '41337471160': Object.freeze({attempts:1,usd:0.05}),
  '41321052351': Object.freeze({attempts:1,usd:0.05}),
  '41306270444': Object.freeze({attempts:1,usd:0.25}),
  '41306121059': Object.freeze({attempts:1,usd:0.25}),
  '41306014229': Object.freeze({attempts:1,usd:0}),
  '41305774289': Object.freeze({attempts:1,usd:0}),
  '41305559593': Object.freeze({attempts:1,usd:0}),
  '41305201610': Object.freeze({attempts:1,usd:0.05}),
  '41304933936': Object.freeze({attempts:1,usd:0.05}),
  '41304857095': Object.freeze({attempts:1,usd:0.25}),
  '41304772544': Object.freeze({attempts:1,usd:0.05}),
});

const PROJECTS = new Set([CONTROL, 'briersystems/montefinance', 'tonyluo2000/explore-studio']);
const fail = code => {throw Object.assign(new Error(code), {code});};

// GitHub run creation is the durable reservation. Unknown/older dispatches
// reserve the full $1 historical ceiling; reviewed-version mock runs reserve
// zero and reviewed-version live runs reserve $0.50. Missing or ambiguous
// history always refuses. Local accounting has a separate fixed $5 share.
async function execute({identity, maximumCostUsd}, callback, runtime) {
  const {env, fetchImpl, now} = runtime;
  const runId = env.GITHUB_RUN_ID, controlSha = env.DEEPSEEK_REVIEWED_CONTROL_SHA;
  if (env.GITHUB_ACTIONS !== 'true' || env.GITHUB_REPOSITORY !== CONTROL || env.GITHUB_JOB !== 'review'
    || env.GITHUB_EVENT_NAME !== 'workflow_dispatch' || !/^\d+$/.test(runId ?? '')
    || env.GITHUB_RUN_ATTEMPT !== '1' || !/^[a-f0-9]{40}$/.test(controlSha ?? '')
    || env.GITHUB_SHA !== controlSha || env.GITHUB_WORKFLOW_SHA !== controlSha
    || env.GITHUB_ACTOR !== 'tonyluo2000' || !env.GH_TOKEN || !env.RUNNER_TEMP) fail('SHARED_LEDGER_UNAVAILABLE');
  if (!PROJECTS.has(identity?.repository) || identity.provider !== 'deepseek' || identity.actualModel !== 'deepseek-v4-pro'
    || identity.taskType !== 'review' || !['low','high'].includes(identity.reasoningEffort)
    || identity.authorizationId !== `gh-run-${runId}` || identity.reviewedControlSha !== controlSha
    || !/^[a-f0-9]{64}$/.test(identity.requestId ?? '') || !/^[a-f0-9]{40}$/.test(identity.baseSha ?? '')
    || !/^[a-f0-9]{40}$/.test(identity.headSha ?? '') || !/^[a-z0-9][a-z0-9-]{0,63}$/.test(identity.taskId ?? '')) fail('HOSTED_IDENTITY_INVALID');
  if (!Number.isFinite(maximumCostUsd) || maximumCostUsd <= 0 || maximumCostUsd > HOSTED_REQUEST_CAP_USD) fail('REQUEST_CAP_EXCEEDED');
  const request = async suffix => {
    const response = await fetchImpl(`https://api.github.com/repos/${CONTROL}/actions/${suffix}`, {
      headers:{Authorization:`Bearer ${env.GH_TOKEN}`, Accept:'application/vnd.github+json', 'X-GitHub-Api-Version':'2022-11-28'},
      signal:AbortSignal.timeout(30000), redirect:'error',
    });
    if (!response.ok) fail('HOSTED_HISTORY_UNAVAILABLE');
    return response.json();
  };
  const current = await request(`runs/${runId}`);
  const createdAt = Date.parse(current.created_at);
  if (String(current.id) !== runId || current.run_attempt !== 1 || current.event !== 'workflow_dispatch'
    || current.path !== WORKFLOW || current.head_sha !== controlSha || current.actor?.login !== 'tonyluo2000'
    || !current.display_title?.startsWith('DeepSeek live |') || !Number.isSafeInteger(current.workflow_id)
    || current.status !== 'in_progress' || !Number.isSafeInteger(current.run_number) || current.run_number < 1
    || !Number.isFinite(createdAt) || createdAt > now || now-createdAt > MAX_DISPATCH_AGE_MS) fail('HOSTED_RUN_INVALID');
  // An accepted dispatch can start late and the remaining job can still use
  // its ten-minute timeout. Keep its reservation through that full margin.
  const cutoff = now - WINDOW_MS - MAX_DISPATCH_AGE_MS - JOB_TIMEOUT_MS;
  const since = new Date(cutoff).toISOString();
  const query = new URLSearchParams({event:'workflow_dispatch', created:`>=${since}`, per_page:'100'});
  const previousQuery = new URLSearchParams({event:'workflow_dispatch',created:`<${since}`,per_page:'1'});
  const [history, previousHistory] = await Promise.all([
    request(`workflows/${current.workflow_id}/runs?${query}`),
    request(`workflows/${current.workflow_id}/runs?${previousQuery}`),
  ]);
  if (!Array.isArray(history.workflow_runs) || !Number.isSafeInteger(history.total_count)
    || history.total_count !== history.workflow_runs.length || history.total_count >= 100) fail('HOSTED_HISTORY_INCOMPLETE');
  if (!Array.isArray(previousHistory.workflow_runs) || !Number.isSafeInteger(previousHistory.total_count)
    || previousHistory.total_count < 0 || previousHistory.workflow_runs.length !== Math.min(previousHistory.total_count,1)) fail('HOSTED_HISTORY_INCOMPLETE');
  const previous = previousHistory.workflow_runs[0];
  if (previous && (previous.workflow_id !== current.workflow_id || previous.event !== 'workflow_dispatch'
    || !Number.isSafeInteger(previous.run_number) || previous.run_number < 1
    || !Number.isFinite(Date.parse(previous.created_at)) || Date.parse(previous.created_at) >= cutoff)) fail('HOSTED_HISTORY_INVALID');
  const ids = new Set();
  const numbers = [];
  let reservedMicros = 0;
  for (const run of history.workflow_runs) {
    const timestamp = Date.parse(run.created_at);
    if (!Number.isSafeInteger(run.id) || ids.has(run.id) || run.workflow_id !== current.workflow_id
      || run.event !== 'workflow_dispatch' || !Number.isFinite(timestamp) || timestamp < cutoff || timestamp > now
      || !Number.isSafeInteger(run.run_attempt) || run.run_attempt < 1
      || !Number.isSafeInteger(run.run_number) || run.run_number < 1
      || run.id === current.id && (run.run_number !== current.run_number || timestamp !== createdAt || run.run_attempt !== 1)) fail('HOSTED_HISTORY_INVALID');
    ids.add(run.id);
    numbers.push(run.run_number);
    const reviewed = run.head_sha === controlSha && run.path === WORKFLOW;
    const legacy = LEGACY_RESERVATIONS[String(run.id)];
    if (legacy) {
      if (run.run_attempt < legacy.attempts) fail('HOSTED_HISTORY_INVALID');
      reservedMicros += Math.ceil(legacy.usd*1000000) + (run.run_attempt-legacy.attempts)*1000000;
    } else {
      const cost = reviewed && run.display_title?.startsWith('DeepSeek mock |') ? 0
        : reviewed && run.display_title?.startsWith('DeepSeek live |') ? HOSTED_REQUEST_CAP_USD : 1;
      reservedMicros += Math.ceil(cost*1000000)*run.run_attempt;
    }
  }
  if (!ids.has(current.id)) fail('HOSTED_HISTORY_INCOMPLETE');
  const first = previous ? previous.run_number + 1 : 1;
  if (numbers.sort((a,b)=>a-b).some((number,index)=>number!==first+index)) fail('HOSTED_HISTORY_INCOMPLETE');
  if (reservedMicros > HOSTED_CAP_USD*1000000) fail('SHARED_WEEKLY_CAP_EXCEEDED');
  const directory = await realpath(env.RUNNER_TEMP);
  if (directory !== path.resolve(env.RUNNER_TEMP) || !(await lstat(directory)).isDirectory()) fail('HOSTED_RESERVATION_PATH_INVALID');
  let handle;
  try {handle = await open(path.join(directory,`deepseek-provider-${runId}.reservation`), constants.O_WRONLY|constants.O_CREAT|constants.O_EXCL|constants.O_NOFOLLOW,0o600);}
  catch (error) {if (error.code === 'EEXIST') fail('PAID_REQUEST_REPLAY_DENIED'); throw error;}
  try {await handle.writeFile(JSON.stringify({runId, authorizationId:identity.authorizationId, requestId:identity.requestId,
    maximumCostUsd, reservedShareUsd:HOSTED_REQUEST_CAP_USD, state:'REQUEST_MAY_HAVE_BEEN_SENT'})+'\n'); await handle.sync();}
  finally {await handle.close();}
  return callback();
}

export const withHostedBudget = (policy, callback) => execute(policy, callback, {env:process.env, fetchImpl:fetch, now:Date.now()});
export function createHostedBudgetTestHarness({env, fetchImpl, now}) {
  if (process.env.NODE_TEST_CONTEXT !== 'child-v8' || typeof fetchImpl !== 'function' || fetchImpl === fetch) fail('TEST_CLIENT_CONTEXT_REQUIRED');
  return (policy, callback) => execute(policy, callback, {env, fetchImpl, now});
}
