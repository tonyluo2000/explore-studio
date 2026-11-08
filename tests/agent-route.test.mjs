import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm, realpath } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { routeTask, primaryCommand, parsePrimaryOutput } from '../scripts/agent-route.mjs';

const REPO='tonyluo2000/mile-commons';
const capabilities={models:[{provider:'openai',model:'gpt-6-luna',family:'openai',efforts:['low','medium','high'],available:'verified',source:'synthetic-test'},{provider:'openai',model:'gpt-6.1-sol',family:'openai',efforts:['low','medium','high'],available:'verified',source:'synthetic-test'},{provider:'openai',model:'gpt-6-astra',family:'openai',efforts:['low','medium','high'],available:'verified',source:'synthetic-test'}]};
async function fixture(t) {
  const root=await realpath(await mkdtemp(path.join(tmpdir(),'route-wrapper-')));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const git=(...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
  git('init');git('config','user.name','Synthetic Test');git('config','user.email','test@example.invalid');git('remote','add','origin',`https://github.com/${REPO}.git`);
  await mkdir(path.join(root,'config'));await writeFile(path.join(root,'config/model-project.json'),JSON.stringify({repository:REPO,activation:'pending_review'}));
  git('add','.');git('commit','-m','synthetic adapter');
  const task={repository:REPO,taskId:'synthetic-docs',taskType:'routine',risk:'low',complexity:'simple',headSha:git('rev-parse','HEAD')};
  return {root,task,git};
}
test('default selects without launching; disabled activation refuses ordinary execution',async t=>{
  const {root,task}=await fixture(t);let calls=0;const launch=async()=>{calls++;};
  const selected=await routeTask({root,task,capabilities,launch});
  assert.equal(selected.status,'planned');assert.equal(selected.route.provider,'openai');assert.equal(selected.route.effectiveEffort,'low');assert.equal(calls,0);
  await assert.rejects(routeTask({root,task,capabilities,launch,execute:true}),/ROUTING_ACTIVATION_APPROVAL_REQUIRED/);assert.equal(calls,0);
});
test('synthetic pilot routes an actual child invocation contract with read-only sandbox and fixed no-source prompt',async t=>{
  const {root,task}=await fixture(t);let calls=0;
  const launch=async command=>{calls++;assert.equal(command.command,'codex');assert.ok(command.args.includes('read-only'));assert.ok(command.args.includes('model_reasoning_effort="low"'));assert.match(command.prompt,/synthetic/);assert.doesNotMatch(command.prompt,/private text/);return {status:'succeeded',output:JSON.stringify({type:'item.completed',item:{type:'agent_message',text:'# Router pilot'}})+'\n'+JSON.stringify({type:'turn.completed',usage:{input_tokens:10,output_tokens:3,cached_input_tokens:0}})};};
  const result=await routeTask({root,task:{...task,instruction:'private text'},capabilities,launch,pilot:true});
  assert.equal(calls,1);assert.equal(result.status,'succeeded');assert.equal(result.outputValidated,true);
  assert.ok(!JSON.stringify(result.record).includes('private text'));assert.ok(!JSON.stringify(result.record).includes('# Router pilot'));
});
test('stale task, wrong project and attempted pilot risk downgrade fail before launch',async t=>{
  const {root,task}=await fixture(t);let calls=0;const launch=async()=>{calls++;};
  await assert.rejects(routeTask({root,task:{...task,headSha:'0'.repeat(40)},capabilities,launch,pilot:true}),/STALE_HEAD/);
  await assert.rejects(routeTask({root,task:{...task,repository:'briersystems/montefinance'},capabilities,launch}),/PROJECT_ADAPTER_MISMATCH/);
  await assert.rejects(routeTask({root,task:{...task,risk:'critical'},capabilities,launch,pilot:true}),/PILOT_REQUIRES_ROUTINE_SYNTHETIC_TASK/);assert.equal(calls,0);
});
test('failed child is never retried or switched; successful wrong output fails pilot',async t=>{
  const {root,task}=await fixture(t);let calls=0;
  const result=await routeTask({root,task,capabilities,pilot:true,launch:async()=>{calls++;return {status:'failed',output:'private provider error'};}});
  assert.equal(result.status,'failed');assert.equal(calls,1);assert.ok(!JSON.stringify(result.record).includes('private provider error'));
  assert.equal((await routeTask({root,task,capabilities,pilot:true,launch:async()=>({status:'succeeded',output:''})})).status,'failed');
});
test('provider command uses explicit supported effort and refuses direct DeepSeek launch',()=>{
  assert.throws(()=>primaryCommand({provider:'deepseek'},{root:'/tmp'}),/GUARDED_DEEPSEEK_PROFILE_REQUIRED/);
  const claude=primaryCommand({provider:'anthropic',model:'claude-sonnet-5-5',effectiveEffort:'medium'},{root:'/tmp',pilot:true});
  assert.ok(claude.args.includes('--effort'));assert.ok(claude.args.includes('--strict-mcp-config'));assert.ok(!claude.args.includes('--dangerously-skip-permissions'));
});
test('usage parsing ignores prompt echo and never labels a requested model as actual',()=>{
  const result=parsePrimaryOutput(JSON.stringify({type:'turn.completed',model:'gpt-6-luna',usage:{input_tokens:10,output_tokens:2}}),'openai');
  assert.equal(result.usage.inputTokens,10);assert.deepEqual(result.execution,{});
});
test('task text cannot opt into DeepSeek, and quota pressure never activates it',async t=>{
  const {root,task}=await fixture(t);
  const now=Date.now();
  const quota={codex:{state:'low',source:'owner',observedAt:now,expiresAt:now+60000}};
  const result=await routeTask({root,task:{...task,ownerRequestedDeepSeek:true},quota,capabilities,now});
  assert.equal(result.route.provider,'openai');
  await assert.rejects(routeTask({root,task:{...task,overrides:{model:'deepseek-v4-pro'}},quota,now}),/DEEPSEEK_OWNER_REQUEST_REQUIRED/);
});
