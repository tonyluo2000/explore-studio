import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveRoute} from '../scripts/deepseek-routing.mjs';
import {ownerQuotaReport} from '../scripts/model-quota.mjs';
import {MODEL_CATALOG} from '../scripts/model-capabilities.mjs';
const repository='tonyluo2000/mile-commons';
const now=Date.parse('2026-11-08T02:00:00Z');
const taskScope={taskId:'task-123',baseSha:'a'.repeat(40),headSha:'b'.repeat(40)};
const grant=(options={})=>({schema:'cross-project.deepseek-owner-request.v1',authorizationId:'owner-test-0001',repository,...taskScope,role:'implementation',model:'deepseek-v4-pro',issuedAt:new Date(now).toISOString(),expiresAt:new Date(now+3600000).toISOString(),authorizationReference:'https://github.com/tonyluo2000/mile-commons/issues/1120#issuecomment-6716279700',...options});
const route=(options={})=>resolveRoute({repository,...taskScope,taskType:'implementation',risk:'low',now,...options});
const report=state=>ownerQuotaReport(state,{now});

test('routine documentation formatting and simple tests use lightweight primary low effort',()=>{
  for(const taskType of ['routine','documentation','formatting','simple-tests']) {
    const selected=route({taskType});
    assert.equal(selected.provider,'openai');assert.equal(selected.model,'gpt-6-luna');assert.equal(selected.reasoningEffort,'low');assert.equal(selected.backupReason,null);
  }
});
test('ordinary code selects low or medium by complexity and task category',()=>{
  assert.equal(route().effectiveEffort,'low');
  for(const taskType of ['feature','bugfix','integration']) assert.equal(route({taskType}).effectiveEffort,'medium');
  assert.equal(route({complexity:'standard'}).effectiveEffort,'medium');
  assert.equal(route({complexity:'multi-file'}).effectiveEffort,'medium');
});
test('architecture and difficult debugging receive primary high reasoning',()=>{
  for(const options of [{taskType:'architecture'},{taskType:'debugging',complexity:'difficult-debugging'}]) {
    const selected=route(options);assert.equal(selected.model,'gpt-6-astra');assert.equal(selected.effectiveEffort,'high');
  }
});
test('unknown risk defaults upward, and sensitive labels raise caller low risk',()=>{
  assert.equal(resolveRoute({repository,taskType:'routine'}).risk,'high');
  for(const taskType of ['security','privacy','financial','tax','authorization','migration','release-tooling']) {
    const selected=route({taskType});assert.equal(selected.risk,'high');assert.equal(selected.effectiveEffort,'high');assert.equal(selected.independentReviewRequired,true);
  }
});
test('healthy primary quota never activates DeepSeek regardless of cost or other role quota',()=>{
  const quota={codex:report('healthy'),claude:report('low')};
  assert.equal(route({quota}).provider,'openai');
  assert.throws(()=>route({quota,overrides:{model:'deepseek-v4-pro'}}),/OWNER_TASK_REQUEST_REQUIRED/);
  assert.equal(route({taskType:'review',implementerFamily:'openai',quota:{codex:report('low'),claude:report('healthy')}}).provider,'anthropic');
});
test('quota constraint alone never activates DeepSeek and blocked primary selects other primary',()=>{
  for(const state of ['low','exhausted','imminent','rate_limited']) {
    const selected=route({quota:{codex:report(state)}});
    assert.notEqual(selected.provider,'deepseek');assert.equal(selected.effectiveEffort,'low');assert.equal(selected.backupReason,null);
    assert.equal(selected.provider,['exhausted','rate_limited'].includes(state)?'anthropic':'openai');
    assert.ok(!selected.reviewer || selected.reviewer.provider!=='deepseek');
  }
});
test('only fresh exact-task owner grant selects guarded Pro under all quota states',()=>{
  for(const quota of [{},{codex:report('healthy')},{codex:report('low')},{codex:report('exhausted')}]) {
    const selected=route({quota,ownerRequest:grant()});
    assert.equal(selected.model,'deepseek-v4-pro');assert.equal(selected.effectiveEffort,'low');assert.equal(selected.backupReason,'EXPLICIT_OWNER_REQUEST');assert.equal(selected.ownerRequestedDeepSeek,true);
    assert.ok(selected.gates.includes('PAID_CALL_AUTHORIZATION_REQUIRED'));assert.ok(selected.gates.includes('EXTERNAL_TRANSFER_AUTHORIZATION_REQUIRED'));
    assert.equal(selected.reviewer.provider,'anthropic');
  }
});
test('model override boolean and prior task approval cannot authorize DeepSeek',()=>{
  for(const quota of [{},{codex:report('low')}]) {
    for(const overrides of [{model:'deepseek-v4-pro'},{provider:'deepseek'},{family:'deepseek'}]) assert.throws(()=>route({quota,overrides}),/OWNER_TASK_REQUEST_REQUIRED/);
  }
  assert.throws(()=>route({ownerRequestedDeepSeek:'true'}),/INVALID_OWNER_DEEPSEEK_REQUEST/);
  assert.throws(()=>route({ownerRequestedDeepSeek:true}),/OWNER_TASK_REQUEST_REQUIRED/);
  for(const request of [grant({taskId:'previous-task'}),grant({headSha:'c'.repeat(40)}),grant({role:'review'}),grant({repository:'briersystems/montefinance'})]) assert.throws(()=>route({ownerRequest:request}),/OWNER_TASK_SCOPE_MISMATCH/);
  assert.throws(()=>route({ownerRequest:grant({expiresAt:new Date(now-1).toISOString()})}),/OWNER_TASK_REQUEST_EXPIRED|INVALID_OWNER_TASK_REQUEST/);
  assert.throws(()=>route({ownerRequest:grant(),overrides:{model:'gpt-6.1-sol'}}),/OWNER_REQUEST_MODEL_CONFLICT/);
});
test('constrained reviewer quota never assigns DeepSeek automatically',()=>{
  for(const state of ['low','exhausted','rate_limited','imminent']) {
    const selected=route({risk:'critical',quota:{claude:report(state)}});
    assert.ok(!selected.reviewer||selected.reviewer.provider!=='deepseek');
    assert.equal(selected.reviewBlocked,true); // Unknown reviewer availability never qualifies a review gate.
  }
  const unavailable=MODEL_CATALOG.map(entry=>({...entry,available:entry.provider==='deepseek'}));
  assert.throws(()=>route({quota:{codex:report('exhausted'),claude:report('exhausted')},capabilities:{models:unavailable}}),/NO_SUITABLE_MODEL/);
});
test('unknown unverified stale and future quota cannot activate a paid provider',()=>{
  for(const codex of [undefined,{state:'low'}, {state:'low',source:'unavailable'}, {...report('low'),expiresAt:new Date(now-1).toISOString()}, {...report('low'),observedAt:new Date(now+1).toISOString()}]) {
    assert.equal(route({quota:{codex}}).provider,'openai');
  }
});
test('critical changes retain high reasoning and independent review under constrained quotas',()=>{
  const selected=route({risk:'critical',quota:{codex:report('exhausted'),claude:report('low')}});
  assert.equal(selected.model,'claude-opus-5-5');assert.equal(selected.effectiveEffort,'high');assert.equal(selected.independentReviewRequired,true);assert.equal(selected.reviewBlocked,true);
  const explicit=route({risk:'critical',ownerRequest:grant(),quota:{codex:report('exhausted'),claude:report('low')}});assert.equal(explicit.model,'deepseek-v4-pro');assert.equal(explicit.effectiveEffort,'high');assert.equal(explicit.independentReviewRequired,true);
  assert.ok(selected.gates.includes('OWNER_RELEASE_APPROVAL_REQUIRED'));
  assert.throws(()=>route({risk:'critical',overrides:{reasoningEffort:'low'}}),/QUALITY_FLOOR_NOT_MET/);
  assert.throws(()=>route({risk:'critical',overrides:{model:'gpt-6-luna'}}),/NO_SUITABLE_MODEL/);
  assert.throws(()=>route({taskType:'security',overrides:{model:'gpt-6-luna',reasoningEffort:'high'}}),/NO_SUITABLE_MODEL/);
});
test('DeepSeek medium is never emitted even for standard features',()=>{
  const selected=route({taskType:'feature',ownerRequest:grant()});
  assert.equal(selected.effectiveEffort,'high');assert.equal(selected.requestedEffort,'medium');assert.equal(selected.reasoningEffort,'high');
  assert.throws(()=>route({ownerRequest:grant(),overrides:{model:'deepseek-v4-pro',reasoningEffort:'medium'}}),/UNSUPPORTED_REASONING_EFFORT/);
});
test('DeepSeek cannot independently review its own implementation',()=>{
  assert.equal(route({taskType:'review',implementerFamily:'deepseek'}).provider,'anthropic');
  assert.throws(()=>route({taskType:'review',implementerFamily:'deepseek',ownerRequest:grant({role:'review'}),overrides:{model:'deepseek-v4-pro'}}),/INDEPENDENT_MODEL_REQUIRED/);
  const blocked=MODEL_CATALOG.map(entry=>({...entry,available:entry.provider==='deepseek'}));
  assert.throws(()=>route({taskType:'review',implementerFamily:'deepseek',quota:{claude:report('low')},capabilities:{models:blocked}}),/INDEPENDENT_MODEL_REQUIRED/);
  assert.throws(()=>route({taskType:'review'}),/IMPLEMENTER_FAMILY_REQUIRED/);
});
test('two grounded failures and substantive review defects escalate before provider change',()=>{
  for(const history of [{failedAttempts:2},{repeatedDefect:true},{criticalInvariantFailed:true},{securityUncertain:true},{privacyUncertain:true},{financialUncertain:true},{substantiveReviewDefect:true}]) {
    const selected=route({history,quota:{codex:report('healthy')}});assert.equal(selected.provider,'openai');assert.equal(selected.effectiveEffort,'high');
  }
});
test('subsequent tasks return to primary without persisting prior explicit DeepSeek request',()=>{
  const active=route({quota:{codex:report('low')}});
  const next=route({quota:{codex:report('healthy')}});
  assert.equal(active.provider,'openai');assert.equal(next.provider,'openai');
  const explicit=route({ownerRequest:grant(),quota:{codex:report('low')}});assert.equal(explicit.provider,'deepseek');assert.equal(next.provider,'openai');assert.equal(explicit.provider,'deepseek');
});
test('owner override selects only documented providers models and supported efforts',()=>{
  assert.equal(route({overrides:{model:'claude-sonnet-5-5',reasoningEffort:'low'}}).provider,'anthropic');
  assert.throws(()=>route({overrides:{model:'codex'}}),/UNSUPPORTED_MODEL/);
  assert.throws(()=>route({overrides:{provider:'untrusted'}}),/UNKNOWN_PROVIDER/);
  assert.throws(()=>route({overrides:{model:'gpt-6.1-sol',provider:'deepseek'}}),/PROVIDER_FAMILY_MISMATCH/);
  assert.throws(()=>route({overrides:{model:'deepseek-flash'}}),/OWNER_TASK_REQUEST_REQUIRED/);
  assert.throws(()=>route({overrides:{approvalAuthority:'OWNER'}}),/INVALID_OVERRIDE/);
  assert.throws(()=>route({complexity:'unknown-or-untrusted'}),/INVALID_COMPLEXITY/);
});
test('unsupported capabilities fall back only to suitable primary and never initiate paid usage',()=>{
  const unavailable=MODEL_CATALOG.map(entry=>({...entry,available:entry.provider!=='openai'}));
  assert.equal(route({capabilities:{models:unavailable}}).provider,'anthropic');
  const onlyBackup=MODEL_CATALOG.map(entry=>({...entry,available:entry.provider==='deepseek'}));
  assert.throws(()=>route({capabilities:{models:onlyBackup}}),/NO_SUITABLE_MODEL/);
  const lowOnly=MODEL_CATALOG.map(entry=>({...entry,efforts:['low']}));
  assert.throws(()=>route({risk:'critical',quota:{codex:report('low')},capabilities:{models:lowOnly}}),/NO_SUITABLE_MODEL/);
});
test('release captain authority remains external and all project adapters share decisions',()=>{
  assert.equal(route({taskType:'release'}).model,null);
  for(const project of ['tonyluo2000/mile-commons','briersystems/montefinance','tonyluo2000/explore-studio']) {
    assert.equal(route({repository:project}).model,'gpt-6.1-sol');assert.equal(route({repository:project}).approvalAuthority,'NONE');
  }
  assert.throws(()=>route({repository:'unknown/project'}),/UNAPPROVED_REPOSITORY/);
});
