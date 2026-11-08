import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,realpath,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createHostedBudgetTestHarness} from '../scripts/deepseek-hosted-budget.mjs';

const now = Date.parse('2026-11-08T12:00:00Z');
const sha = 'a'.repeat(40);
async function fixture(t, change = {}) {
  const directory = await realpath(await mkdtemp(path.join(os.tmpdir(),'deepseek-hosted-')));
  t.after(()=>rm(directory,{recursive:true,force:true}));
  const current = {id:42,workflow_id:7,run_attempt:1,run_number:1,event:'workflow_dispatch',path:'.github/workflows/deepseek-review.yml',
    head_sha:sha,actor:{login:'tonyluo2000'},display_title:'DeepSeek live | review',status:'in_progress',created_at:new Date(now-1000).toISOString()};
  const env = {GITHUB_ACTIONS:'true',GITHUB_REPOSITORY:'tonyluo2000/mile-commons',GITHUB_JOB:'review',
    GITHUB_EVENT_NAME:'workflow_dispatch',GITHUB_RUN_ID:'42',GITHUB_RUN_ATTEMPT:'1',GITHUB_SHA:sha,GITHUB_WORKFLOW_SHA:sha,
    GITHUB_ACTOR:'tonyluo2000',DEEPSEEK_REVIEWED_CONTROL_SHA:sha,GH_TOKEN:'synthetic',RUNNER_TEMP:directory,...change.env};
  const runs = (change.runs ?? [current]).map((row,index)=>({...row,run_number:change.runNumbers?.[index]??index+1}));
  const fetchImpl = async url => ({ok:true,json:async()=>{
    if (!url.includes('/workflows/')) return {...current,run_number:runs.find(row=>row.id===current.id)?.run_number??1,...change.current};
    if (new URL(url).searchParams.get('created').startsWith('<')) {
      return {total_count:change.previous?1:0,workflow_runs:change.previous?[change.previous]:[]};
    }
    return {total_count:change.totalCount??runs.length,workflow_runs:runs};
  }});
  return {current,env,policy:{identity:{repository:'tonyluo2000/mile-commons',provider:'deepseek',actualModel:'deepseek-v4-pro',
    taskType:'review',taskId:'pr-1-review',baseSha:sha,headSha:sha,reviewedControlSha:sha,reasoningEffort:'high',authorizationId:'gh-run-42',requestId:'b'.repeat(64)},maximumCostUsd:.5},
    invoke:createHostedBudgetTestHarness({env,fetchImpl,now})};
}
test('one reviewed owner dispatch reserves durably before callback and cannot repeat',async t=>{
  const f=await fixture(t);let calls=0;
  assert.equal(await f.invoke(f.policy,async()=>{calls++;return 'ok';}),'ok');
  await assert.rejects(f.invoke(f.policy,async()=>{calls++;}),{code:'PAID_REQUEST_REPLAY_DENIED'});
  assert.equal(calls,1);
});
test('failed or ambiguous callback keeps the one-use reservation',async t=>{
  const f=await fixture(t);let calls=0;
  await assert.rejects(f.invoke(f.policy,async()=>{calls++;throw Error('synthetic failure');}));
  await assert.rejects(f.invoke(f.policy,async()=>{calls++;}),{code:'PAID_REQUEST_REPLAY_DENIED'});
  assert.equal(calls,1);
});
test('hosted context and workflow reruns refuse before callback',async t=>{
  for(const change of [{env:{GITHUB_RUN_ATTEMPT:'2'}},{env:{GITHUB_ACTOR:'another-user'}},
    {env:{GH_TOKEN:''}},{current:{head_sha:'c'.repeat(40)}},{current:{display_title:'DeepSeek mock | review'}}]) {
    const f=await fixture(t,change);let calls=0;
    await assert.rejects(f.invoke(f.policy,async()=>calls++));assert.equal(calls,0);
  }
});
test('missing, duplicate and incomplete run history never reset budget to zero',async t=>{
  const base=await fixture(t);
  for(const change of [{runs:[]},{runs:[base.current,base.current]}, {totalCount:2}]) {
    const f=await fixture(t,change);let calls=0;
    await assert.rejects(f.invoke(f.policy,async()=>calls++));assert.equal(calls,0);
  }
});
test('reviewed live runs cap at hosted five dollars and old runs reserve one dollar',async t=>{
  const f=await fixture(t);
  const rows=Array.from({length:10},(_,index)=>({...f.current,id:index===0?42:100+index}));
  const atCap=await fixture(t,{runs:rows});assert.equal(await atCap.invoke(atCap.policy,async()=>1),1);
  const overCap=await fixture(t,{runs:[...rows,{...f.current,id:999}]});
  await assert.rejects(overCap.invoke(overCap.policy,async()=>assert.fail()),{code:'SHARED_WEEKLY_CAP_EXCEEDED'});
  const old=rows.slice(0,6).map((row,index)=>index?{...row,head_sha:'c'.repeat(40)}:row);
  const conservative=await fixture(t,{runs:old});
  await assert.rejects(conservative.invoke(conservative.policy,async()=>assert.fail()),{code:'SHARED_WEEKLY_CAP_EXCEEDED'});
});
test('only this reviewed workflow version can classify a mock as unpaid',async t=>{
  const f=await fixture(t);
  const rows=[f.current,...Array.from({length:15},(_,index)=>({...f.current,id:100+index,display_title:'DeepSeek mock | review'}))];
  const mocks=await fixture(t,{runs:rows});assert.equal(await mocks.invoke(mocks.policy,async()=>1),1);
});
test('stricter request cap and hosted authorization namespace are enforced',async t=>{
  const f=await fixture(t);
  await assert.rejects(f.invoke({...f.policy,maximumCostUsd:.51},async()=>assert.fail()),{code:'REQUEST_CAP_EXCEEDED'});
  await assert.rejects(f.invoke({...f.policy,identity:{...f.policy.identity,authorizationId:'local-call'}},async()=>assert.fail()),{code:'HOSTED_IDENTITY_INVALID'});
});
test('reconciled legacy preflights are zero only for the inspected attempt',async t=>{
  const f=await fixture(t);
  const full=Array.from({length:10},(_,index)=>({...f.current,id:index===0?42:100+index}));
  const old={...f.current,id:42232247157,head_sha:'c'.repeat(40),display_title:'DeepSeek PR review (manual)',run_attempt:1};
  const known=await fixture(t,{runs:[...full,old]});assert.equal(await known.invoke(known.policy,async()=>1),1);
  const rerun=await fixture(t,{runs:[...full,{...old,run_attempt:2}]});
  await assert.rejects(rerun.invoke(rerun.policy,async()=>assert.fail()),{code:'SHARED_WEEKLY_CAP_EXCEEDED'});
});
test('run numbers detect missing history at the budget boundary and within the window',async t=>{
  const f=await fixture(t);
  const previous={...f.current,id:1,run_number:1,created_at:new Date(now-169*60*60*1000).toISOString()};
  const intact=await fixture(t,{previous,runNumbers:[2]});
  assert.equal(await intact.invoke(intact.policy,async()=>1),1);
  const boundaryGap=await fixture(t,{previous,runNumbers:[3]});
  await assert.rejects(boundaryGap.invoke(boundaryGap.policy,async()=>assert.fail()),{code:'HOSTED_HISTORY_INCOMPLETE'});
  const internalGap=await fixture(t,{previous,runs:[f.current,{...f.current,id:43}],runNumbers:[2,4]});
  await assert.rejects(internalGap.invoke(internalGap.policy,async()=>assert.fail()),{code:'HOSTED_HISTORY_INCOMPLETE'});
});
test('late dispatch refuses and the reservation window includes its possible execution delay',async t=>{
  const f=await fixture(t);
  const late=await fixture(t,{current:{created_at:new Date(now-31*60*1000).toISOString()}});
  await assert.rejects(late.invoke(late.policy,async()=>assert.fail()),{code:'HOSTED_RUN_INVALID'});
  const previous=Array.from({length:10},(_,index)=>({...f.current,id:100+index,
    created_at:new Date(now-(168*60+20)*60*1000).toISOString()}));
  const f2=await fixture(t,{runs:[...previous,f.current]});
  await assert.rejects(f2.invoke(f2.policy,async()=>assert.fail()),{code:'SHARED_WEEKLY_CAP_EXCEEDED'});
});
