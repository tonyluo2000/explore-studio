import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm, realpath } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { sourcePolicyDigest } from '../scripts/model-activation.mjs';
import { routeTask, primaryCommand, parsePrimaryOutput, main } from '../scripts/agent-route.mjs';

const REPO='tonyluo2000/mile-commons';
const capabilities={models:[{provider:'openai',model:'gpt-6-luna',family:'openai',efforts:['low','medium','high'],available:'verified',source:'synthetic-test'},{provider:'openai',model:'gpt-6.1-sol',family:'openai',efforts:['low','medium','high'],available:'verified',source:'synthetic-test'},{provider:'openai',model:'gpt-6-astra',family:'openai',efforts:['low','medium','high'],available:'verified',source:'synthetic-test'}]};
async function fixture(t) {
  const root=await realpath(await mkdtemp(path.join(tmpdir(),'route-wrapper-')));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const git=(...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
  git('init');git('config','user.name','Synthetic Test');git('config','user.email','test@example.invalid');git('remote','add','origin',`https://github.com/${REPO}.git`);
  await mkdir(path.join(root,'config'));await writeFile(path.join(root,'config/model-project.json'),JSON.stringify({repository:REPO,activationPolicy:'reviewed-owner-record-required'}));
  git('add','.');git('commit','-m','synthetic adapter');
  const task={repository:REPO,taskId:'synthetic-docs',taskType:'routine',risk:'low',complexity:'simple',baseSha:git('rev-parse','HEAD'),headSha:git('rev-parse','HEAD')};
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
  await assert.rejects(routeTask({root,task:{...task,overrides:{model:'deepseek-v4-pro'}},quota,now}),/OWNER_TASK_REQUEST_REQUIRED/);
});

const scopedRequest=(task,now=Date.now(),options={})=>({schema:'cross-project.deepseek-owner-request.v1',authorizationId:'owner-test-0001',repository:task.repository,taskId:task.taskId,role:'implementation',baseSha:task.baseSha,headSha:task.headSha,model:'deepseek-v4-pro',issuedAt:new Date(now).toISOString(),expiresAt:new Date(now+3600000).toISOString(),authorizationReference:'https://github.com/tonyluo2000/mile-commons/issues/1120#issuecomment-6716279700',...options});
test('fresh operator request selects guarded DeepSeek but untrusted task request cannot opt in',async t=>{
  const {root,task}=await fixture(t);const now=Date.now();const ownerRequest=scopedRequest(task,now);
  const untrusted=await routeTask({root,task:{...task,ownerRequest,ownerRequestedDeepSeek:true},capabilities,now});assert.equal(untrusted.route.provider,'openai');
  await assert.rejects(routeTask({root,task,ownerRequestedDeepSeek:true,now}),/OWNER_TASK_REQUEST_REQUIRED/);
  const selected=await routeTask({root,task,ownerRequest,now});assert.equal(selected.route.model,'deepseek-v4-pro');assert.equal(selected.route.ownerAuthorizationId,'owner-test-0001');
  assert.ok(!JSON.stringify(selected.record).includes('authorizationReference'));
  await assert.rejects(routeTask({root,task:{...task,taskId:'other-task'},ownerRequest,now}),/OWNER_TASK_SCOPE_MISMATCH/);
  await assert.rejects(routeTask({root,task,ownerRequest:scopedRequest(task,now,{headSha:'a'.repeat(40)}),now}),/OWNER_TASK_SCOPE_MISMATCH/);
});
test('unverified availability and exhausted capacity refuse execution before child launch',async t=>{
  const {root,task}=await fixture(t);let calls=0;const launch=async()=>{calls++;};
  const unknown={models:capabilities.models.map(value=>({...value,available:'unknown'}))};
  await assert.rejects(routeTask({root,task,capabilities:unknown,pilot:true,launch}),/MODEL_AVAILABILITY_UNVERIFIED/);assert.equal(calls,0);
  const now=Date.now();const quota={codex:{state:'exhausted',source:'owner',observedAt:now,expiresAt:now+60000},claude:{state:'exhausted',source:'owner',observedAt:now,expiresAt:now+60000}};
  await assert.rejects(routeTask({root,task,quota,capabilities,pilot:true,launch,now}),/NO_SUITABLE_MODEL/);assert.equal(calls,0);
  assert.deepEqual(parsePrimaryOutput(JSON.stringify({type:'thread.started',thread:{model:'gpt-6-luna',reasoningEffort:'low'}}),'openai').execution,{});
});
test('CLI refuses obsolete broad opt-in flag and requires owner request filename',async()=>{
  await assert.rejects(main(['--use-deepseek-pro']),/INVALID_ARGUMENT/);
  await assert.rejects(main(['--owner-request']),/INVALID_ARGUMENT/);
});
test('CLI reads operator request separately and records only an advisory DeepSeek selection',async t=>{
  const {root,task}=await fixture(t);const filename=path.join(root,'task.json');const requestFile=path.join(root,'owner-request.json');
  await writeFile(filename,JSON.stringify(task));await writeFile(requestFile,JSON.stringify(scopedRequest(task)));
  const originalCwd=process.cwd(),originalLog=console.log;const lines=[];
  try {
    process.chdir(root);console.log=value=>lines.push(value);
    await main(['--task',filename,'--owner-request',requestFile]);
  } finally {process.chdir(originalCwd);console.log=originalLog;}
  assert.equal(lines.length,1);const receipt=JSON.parse(lines[0]);
  assert.equal(receipt.status,'planned');assert.equal(receipt.requested.model,'deepseek-v4-pro');assert.equal(receipt.actual.model,null);
  assert.equal(receipt.selectionAvailability,'unknown');assert.equal(receipt.limitation,'MODEL_AVAILABILITY_UNVERIFIED');
  assert.ok(!lines[0].includes('authorizationReference'));
});

test('approved primary capability can launch without editing source, while DeepSeek still needs separate grants',async t=>{
 const {root,task}=await fixture(t);let calls=0;const digest=sourcePolicyDigest();
 const activation={schema:'cross-project.primary-routing-activation.v1',repository:task.repository,activationId:'synthetic-activation-01',ownerApproved:true,ownerApprovalReference:'synthetic:test-only',sourcePolicyDigest:digest,roles:['implementation','review'],independentReview:{provider:'anthropic',actualModel:'claude-opus-5-5',outcome:'clean',substantiveDefects:0,participatedInImplementation:false,sourcePolicyDigest:digest,baseSha:'a'.repeat(40),headSha:'b'.repeat(40),receiptSha256:'c'.repeat(64),sourceBundleSha256:'d'.repeat(64)}};
 const result=await routeTask({root,task:{...task,instruction:'Perform a synthetic task.'},activation,capabilities,execute:true,launch:async()=>{calls++;return {status:'succeeded',output:''};}});
 assert.equal(calls,1);assert.equal(result.route.provider,'openai');assert.equal(result.status,'succeeded');
});


test('adapter descriptions cannot select another activation schema or grant execution', async t => {
  const {root,task} = await fixture(t);
  await writeFile(path.join(root,'config/model-project.json'),JSON.stringify({
    repository:REPO,
    activationPolicy:'active',
    primaryActivationRecordSchema:'cross-project.primary-routing-activation.v999',
    sourcePolicy:'scripts/untrusted.mjs',
    releaseAuthority:'synthetic description only',
  }));
  let calls = 0;
  const launch = async () => { calls++; return {status:'succeeded',output:''}; };
  const options = {root,task:{...task,instruction:'Perform a synthetic task.'},capabilities,execute:true,launch};
  await assert.rejects(routeTask(options),{code:'ROUTING_ACTIVATION_APPROVAL_REQUIRED'});
  const digest = sourcePolicyDigest();
  const activation = {
    schema:'cross-project.primary-routing-activation.v999',repository:REPO,
    activationId:'synthetic-adapter-test',ownerApproved:true,
    ownerApprovalReference:'synthetic:test-only',sourcePolicyDigest:digest,
    roles:['implementation','review'],
    independentReview:{provider:'anthropic',actualModel:'claude-opus-5-5',outcome:'clean',
      substantiveDefects:0,participatedInImplementation:false,sourcePolicyDigest:digest,
      baseSha:'a'.repeat(40),headSha:'b'.repeat(40),receiptSha256:'c'.repeat(64),sourceBundleSha256:'d'.repeat(64)},
  };
  await assert.rejects(routeTask({...options,activation}),{code:'ROUTING_ACTIVATION_APPROVAL_REQUIRED'});
  assert.equal(calls,0);
  activation.schema = 'cross-project.primary-routing-activation.v1';
  const result = await routeTask({...options,activation});
  assert.equal(result.status,'succeeded');
  assert.equal(result.route.provider,'openai');
  assert.equal(calls,1);
});
