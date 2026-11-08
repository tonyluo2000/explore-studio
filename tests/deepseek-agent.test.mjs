import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,mkdir,readFile,rm,symlink,realpath} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {prepareImplementation as guardedPrepareImplementation,runImplementation as guardedRunImplementation,validateImplementationResponse,applyImplementation,createIsolatedWorktree,executeImplementationWithReceipt,finalizeImplementationResult} from '../scripts/deepseek-agent.mjs';
const constrainedQuota = () => ({codex:{state:'low',source:'owner',observedAt:new Date().toISOString(),expiresAt:new Date(Date.now()+3_600_000).toISOString()}});
const prepareImplementation = options => guardedPrepareImplementation({routingContext:{ownerRequestedDeepSeek:true,quota:constrainedQuota(),risk:'low',complexity:'routine'},...options});
const runImplementation = options => guardedRunImplementation({routingContext:{ownerRequestedDeepSeek:true,quota:constrainedQuota(),risk:'low',complexity:'routine'},...options});
async function fixture(t){
 const root=await realpath(await mkdtemp(path.join(tmpdir(),'deepseek-agent-'))); t.after(()=>rm(root,{recursive:true,force:true}));
 const git=(...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
 git('init','-b','codex/deepseek-test');git('config','user.name','Synthetic Test');git('config','user.email','test@example.invalid');git('remote','add','origin','https://github.com/tonyluo2000/mile-commons.git');
 await mkdir(path.join(root,'lib'));await writeFile(path.join(root,'lib/average.mjs'),'export const average = values => values.reduce((a,b)=>a+b,0) / values.length;\n');git('add','.');git('commit','-m','synthetic source');
 const sha=git('rev-parse','HEAD');
 const manifest={schema:'cross-project.deepseek-implementation.v1',repository:'tonyluo2000/mile-commons',taskId:'average-empty-guard',title:'Guard empty arrays',instruction:'Return zero for an empty array.',baseSha:sha,headSha:sha,ownedPaths:['lib/average.mjs'],contextPaths:[],tests:[]};
 return {root,manifest,git};
}
test('mock explores exact selected source without provider calls or fabricated actual model',async t=>{
 const {root,manifest}=await fixture(t);let calls=0;
 const result=await runImplementation({root,manifest,providerCall:()=>{calls++;throw Error('must not call');}});
 assert.equal(calls,0);assert.equal(result.status,'MOCK_ONLY');assert.equal(result.actualModel,null);assert.equal(result.chargesUsd,null);
 assert.equal(result.gateEffect,'NONE');assert.ok(result.requestId);
});
test('validated proposal can modify exclusively owned source in clean isolated lane',async t=>{
 const {root,manifest}=await fixture(t);const prepared=await prepareImplementation({root,manifest});
 const proposal={summary:'Guarded an empty input.',changes:[{path:'lib/average.mjs',original_sha256:prepared.sources[0].sha256,content:'export const average = values => values.length ? values.reduce((a,b)=>a+b,0) / values.length : 0;\n'}]};
 const files=await applyImplementation({root,prepared,proposal});assert.deepEqual(files,['lib/average.mjs']);
 assert.match(await readFile(path.join(root,'lib/average.mjs'),'utf8'),/: 0/);
 await assert.rejects(applyImplementation({root,prepared,proposal}),/WORKTREE_NOT_CLEAN/);
});
test('rejects unowned paths, stale hashes, duplicate replacements and extra model commands',async t=>{
 const {root,manifest}=await fixture(t);const prepared=await prepareImplementation({root,manifest});
 const change={path:'lib/average.mjs',original_sha256:prepared.sources[0].sha256,content:'export const answer = 0;\n'};
 for(const proposal of [
  {summary:'test',changes:[{...change,path:'lib/other.mjs'}]},
  {summary:'test',changes:[{...change,original_sha256:'bad'}]},
  {summary:'test',changes:[change,change]},
  {summary:'test',changes:[change],command:'git push'}
 ]) assert.throws(()=>validateImplementationResponse(proposal,prepared));
});
test('rejects stale head, dirty source, symlinks and unapproved repository identity',async t=>{
 const {root,manifest,git}=await fixture(t);
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,headSha:'0'.repeat(40)}}),/STALE_HEAD/);
 await writeFile(path.join(root,'lib/average.mjs'),'owner uncommitted changes\n');
 await assert.rejects(prepareImplementation({root,manifest}),/UNCOMMITTED_SOURCE_CHANGE/);
 git('checkout','--','lib/average.mjs'); await symlink('average.mjs',path.join(root,'lib/link.mjs'));
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,ownedPaths:['lib/link.mjs']}}));
 git('remote','set-url','origin','https://github.com/other/repository.git');await assert.rejects(prepareImplementation({root,manifest}),/REPOSITORY_IDENTITY_MISMATCH/);
});
test('live mode refuses absent exact-call approval before provider and caps cost',async t=>{
 const {root,manifest}=await fixture(t);let calls=0;
 await assert.rejects(runImplementation({root,manifest,mode:'live',providerCall:()=>{calls++;}}),/EXACT_CALL_APPROVAL_REQUIRED/);
 assert.equal(calls,0);
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,maxCostUsd:1.01}}),/REQUEST_CAP_EXCEEDED/);
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,tests:[{kind:'shell',files:['tests/x.py']}]}}),/INVALID_TESTS/);
});
test('worktree creation does not reset existing destinations or unrelated branches',async t=>{
 const {root,manifest}=await fixture(t);const destination=path.join(root,'lane');
 assert.equal(createIsolatedWorktree({root,destination,branch:'codex/deepseek-child',baseSha:manifest.headSha}),destination);
 assert.throws(()=>createIsolatedWorktree({root,destination,branch:'codex/deepseek-child',baseSha:manifest.headSha}));
});
test('concurrent owner edit between preflight and open is refused without overwrite',async t=>{
 const {root,manifest}=await fixture(t);const prepared=await prepareImplementation({root,manifest});
 const proposal={summary:'Bounded change.',changes:[{path:'lib/average.mjs',original_sha256:prepared.sources[0].sha256,content:'export const average = () => 0;\n'}]};
 await assert.rejects(applyImplementation({root,prepared,proposal,beforeOpen:()=>writeFile(path.join(root,'lib/average.mjs'),'owner concurrent edit\n')}),/SOURCE_CHANGED_DURING_APPLY/);
 assert.equal(await readFile(path.join(root,'lib/average.mjs'),'utf8'),'owner concurrent edit\n');
});
test('new owned files are allowed without granting unowned creation',async t=>{
 const {root,manifest}=await fixture(t);manifest.ownedPaths=['lib/empty-average.mjs'];
 const prepared=await prepareImplementation({root,manifest});assert.equal(prepared.sources[0].sha256,null);
 const proposal={summary:'Added a source helper.',changes:[{path:manifest.ownedPaths[0],original_sha256:null,content:'export const emptyAverage = 0;\n'}]};
 await applyImplementation({root,prepared,proposal});
 assert.equal(await readFile(path.join(root,manifest.ownedPaths[0]),'utf8'),proposal.changes[0].content);
});

test('all primary quota states refuse DeepSeek without an explicit owner request',async t=>{
 const {root,manifest}=await fixture(t);let calls=0;
 for(const quota of [{},...['healthy','low','exhausted','rate_limited','imminent'].map(state=>({codex:{...constrainedQuota().codex,state}}))]) {
  await assert.rejects(guardedRunImplementation({root,manifest,mode:'live',routingContext:{quota},providerCall:()=>{calls++;}}));
 }
 assert.equal(calls,0);
});
test('unknown source remains fail-closed under an explicit owner DeepSeek request',async t=>{
 const {root,manifest}=await fixture(t);let calls=0;
 await assert.rejects(runImplementation({root,manifest:{...manifest,ownedPaths:['mobile/private/health.json']},mode:'live',providerCall:()=>{calls++;}}),/PATH_NOT_ALLOWLISTED/);
 assert.equal(calls,0);
});
test('difficult backup tasks serialize high effort and never provider medium',async t=>{
 const {root,manifest}=await fixture(t);
 const prepared=await prepareImplementation({root,manifest,routingContext:{ownerRequestedDeepSeek:true,quota:constrainedQuota(),complexity:'complex',risk:'high'}});
 assert.equal(prepared.route.reasoningEffort,'high');
 assert.equal(prepared.request.requestBody.reasoning_effort,'high');
});

test('implementation manifest cannot activate using a reviewer role or quota',async t=>{
 const {root,manifest}=await fixture(t);
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,taskType:'review'}}),/IMPLEMENTATION_ROLE_REQUIRED/);
 await assert.rejects(prepareImplementation({root,manifest,routingContext:{role:'review',quota:constrainedQuota()}}),/IMPLEMENTATION_ROLE_REQUIRED/);
});


test('control-plane ownership is denied without an override',async t=>{
 const {root,manifest}=await fixture(t);
 for(const filename of ['AGENTS.md','.github/workflows/release.yml','package.json','config/routing.json','scripts/deepseek-review-core.mjs','scripts/with-project-node.sh','scripts/agent-route.mjs','scripts/model-quota.mjs','scripts/model-quality.mjs','scripts/model-capabilities.mjs','scripts/model-telemetry.mjs']) {
  await assert.rejects(prepareImplementation({root,manifest:{...manifest,ownedPaths:[filename]}}),/CONTROL_PLANE_WRITE_DENIED/);
 }
});
test('receipt and proposal reserve before any callback, outside repo, without symlinks',async t=>{
 const {root,manifest}=await fixture(t);const outside=await realpath(await mkdtemp(path.join(tmpdir(),'agent-receipts-')));t.after(()=>rm(outside,{recursive:true,force:true}));
 let calls=0;const run=async()=>{calls++;return {status:'MOCK_ONLY'};};
 const output=path.join(outside,'one.json');await writeFile(output,'existing receipt');
 await assert.rejects(executeImplementationWithReceipt({root,manifest,output,run}),/EEXIST/);assert.equal(calls,0);assert.equal(await readFile(output,'utf8'),'existing receipt');
 await assert.rejects(executeImplementationWithReceipt({root,manifest,output:path.join(root,'receipt.json'),run}),/OUTSIDE_REPOSITORY/);assert.equal(calls,0);
 await symlink(outside,path.join(outside,'link'));
 await assert.rejects(executeImplementationWithReceipt({root,manifest,output:path.join(outside,'link','two.json'),run}),/OUTPUT_SYMLINK_DENIED/);assert.equal(calls,0);
 const reserved=path.join(outside,'reserved.json');await writeFile(reserved+'.proposal.json','prior proposal');
 const refusal=await executeImplementationWithReceipt({root,manifest,output:reserved,run});assert.equal(refusal.status,'EXECUTION_FAILED');assert.equal(calls,0);
});
test('post-provider schema failure preserves attested usage in finalized offline receipt',async t=>{
 const {root,manifest}=await fixture(t);const prepared=await prepareImplementation({root,manifest});
 const usage={prompt_tokens:20,completion_tokens:10,total_tokens:30};
 const report={mode:'OFFLINE_TEST',requestId:prepared.requestId,status:'RESERVED',actualModel:null,usage:null};
 await finalizeImplementationResult({root,prepared,report,result:{resolvedModel:prepared.route.model,usage,parsed:{summary:'test',changes:[],unsafe:'private raw output must not persist'}}});
 assert.equal(report.status,'POST_PROVIDER_FAILED');assert.deepEqual(report.usage,usage);assert.equal(report.actualModel,prepared.route.model);assert.equal(report.requestId,prepared.requestId);assert.doesNotMatch(JSON.stringify(report),/private raw output/);
 const outside=await realpath(await mkdtemp(path.join(tmpdir(),'agent-failure-')));t.after(()=>rm(outside,{recursive:true,force:true}));
 const output=path.join(outside,'failure.json');await executeImplementationWithReceipt({root,manifest,output,run:async()=>report});
 const receipt=JSON.parse(await readFile(output,'utf8'));assert.equal(receipt.status,'POST_PROVIDER_FAILED');assert.deepEqual(receipt.usage,usage);
});
test('apply leaves model-authored code unexecuted and reports suggested argv only',async t=>{
 const {root,manifest}=await fixture(t);manifest.tests=[{kind:'node-test',files:['tests/danger.test.mjs']}];const prepared=await prepareImplementation({root,manifest});
 const report={mode:'OFFLINE_TEST',requestId:prepared.requestId};
 const result={resolvedModel:prepared.route.model,usage:{prompt_tokens:1,completion_tokens:1,total_tokens:2},parsed:{summary:'Bounded source change.',changes:[{path:'lib/average.mjs',original_sha256:prepared.sources[0].sha256,content:'throw new Error("must never execute model code");\n'}]}};
 await finalizeImplementationResult({root,prepared,report,result,apply:true});assert.equal(report.status,'APPLIED_UNTESTED');assert.equal(report.tests[0].status,'NOT_RUN');assert.ok(report.tests[0].argv.includes('tests/danger.test.mjs'));
});

test('model-only manifest cannot impersonate explicit owner DeepSeek selection',async t=>{
 const {root,manifest}=await fixture(t);
 for(const ownerRequestedDeepSeek of [undefined,false,'true']) {
  await assert.rejects(guardedPrepareImplementation({root,manifest:{...manifest,model:'deepseek-v4-pro'},routingContext:{ownerRequestedDeepSeek,quota:constrainedQuota(),risk:'low',complexity:'routine'}}),{code:'DEEPSEEK_OWNER_REQUEST_REQUIRED'});
 }
});
test('explicit owner request can prepare a bounded task when primary quota is unknown',async t=>{
 const {root,manifest}=await fixture(t);
 const prepared=await guardedPrepareImplementation({root,manifest,routingContext:{ownerRequestedDeepSeek:true,risk:'low',complexity:'routine'}});
 assert.equal(prepared.route.model,'deepseek-v4-pro');assert.equal(prepared.request.requestBody.reasoning_effort,'low');
});
