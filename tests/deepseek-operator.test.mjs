import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,realpath,rm,symlink,stat,access} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {sourcePolicyDigest} from '../scripts/model-activation.mjs';
import {planImplementation} from '../scripts/deepseek-agent.mjs';
import {TASK_SCHEMA,prepareDecisionCard,executeDecisionCard,createDeepSeekOperatorTestHarness,readOperatorFile} from '../scripts/deepseek.mjs';
const repository='tonyluo2000/mile-commons';
async function fixture(t) {
 const root=await realpath(await mkdtemp(path.join(tmpdir(),'deepseek-operator-source-'))),outside=await realpath(await mkdtemp(path.join(tmpdir(),'deepseek-operator-records-')));t.after(()=>Promise.all([rm(root,{recursive:true,force:true}),rm(outside,{recursive:true,force:true})]));
 const git=(...args)=>execFileSync('git',['-C',root,'-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','-c','user.name=Synthetic','-c','user.email=fixture@example.com',...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trimEnd();
 git('init','-qb','codex/deepseek-operator');git('remote','add','origin',`https://github.com/${repository}`);await mkdir(path.join(root,'lib'));await writeFile(path.join(root,'lib/source.mjs'),'export const value = 1;\n');git('add','.');git('commit','-qm','Synthetic base');const baseSha=git('rev-parse','HEAD');await writeFile(path.join(root,'lib/source.mjs'),'export const value = 2;\n');git('add','.');git('commit','-qm','Synthetic task');const headSha=git('rev-parse','HEAD');
 const implementation={schema:TASK_SCHEMA,repository,taskId:'synthetic-implementation',role:'implementation',baseSha,headSha,risk:'low',complexity:'routine',title:'Bounded source update',instruction:'Prepare a bounded source change.',ownedPaths:['lib/source.mjs'],tests:[{kind:'node-test',files:['tests/focused.test.mjs']}]};
 const review={schema:TASK_SCHEMA,repository,taskId:'pr-12-review',role:'review',pullNumber:12,baseSha,headSha,risk:'low',complexity:'routine',implementerFamily:'openai'};
 const diff=git('diff','--no-ext-diff','--no-textconv','--no-renames','--unified=3',baseSha,headSha)+'\n';const files=[{filename:'lib/source.mjs',additions:1,deletions:1}];
 const github={getPull:async()=>({state:'open',base:{sha:baseSha},head:{sha:headSha},title:'Synthetic title',body:'Synthetic body'}),getComparison:async()=>({complete:true,baseSha,headSha,mergeBaseSha:baseSha,totalCommits:1,status:'ahead',diff,files})};
 return {root,outside,git,implementation,review,github};
}
const approve=card=>({...card,ownerRequested:true,transferApproved:true,paymentApproved:true,authorizationReference:'owner:synthetic-specific-task'});
function standing() {
 const digest=sourcePolicyDigest();return {schema:'cross-project.deepseek-activation.v1',repository,activationId:'synthetic-operator-standing',ownerApproved:true,ownerApprovalReference:'owner:synthetic-standing-policy',sourcePolicyDigest:digest,roles:['implementation','review'],independentReview:{provider:'anthropic',actualModel:'claude-opus-5-5',outcome:'clean',substantiveDefects:0,participatedInImplementation:false,sourcePolicyDigest:digest,baseSha:'a'.repeat(40),headSha:'b'.repeat(40),receiptSha256:'c'.repeat(64),sourceBundleSha256:'d'.repeat(64)}};
}
test('both role plans produce one exact non-authorizing card without a provider call',async t=>{
 const data=await fixture(t);const originalFetch=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;throw new Error('planning must never call a provider');};
 try {for(const task of [data.implementation,data.review]) {const card=await prepareDecisionCard({root:data.root,task,github:data.github});assert.equal(card.ownerRequested,false);assert.equal(card.transferApproved,false);assert.equal(card.paymentApproved,false);assert.equal(card.model,'deepseek-v4-pro');assert.equal(card.effectiveEffort,'low');assert.equal(card.destination,'https://api.deepseek.com/chat/completions');assert.equal(card.inventory.length,1);assert.equal(card.inventory[0].path,'lib/source.mjs');assert.match(card.bodySha256,/^[a-f0-9]{64}$/);assert.match(card.requestSha256,/^[a-f0-9]{64}$/);assert.equal(card.automaticRetries,0);assert.equal(card.testExecution,'HANDOFF_ONLY');assert.equal(card.applyChanges,false);assert.doesNotMatch(JSON.stringify(card),/Prepare a bounded source change/);}assert.equal(calls,0);}finally{globalThis.fetch=originalFetch;}
});
test('advisory implementation source plan carries no owner authority',async t=>{
 const data=await fixture(t);const task=data.implementation;const prepared=await planImplementation({root:data.root,manifest:{schema:'cross-project.deepseek-implementation.v1',repository,taskId:task.taskId,baseSha:task.baseSha,headSha:task.headSha,title:task.title,instruction:task.instruction,ownedPaths:task.ownedPaths},routingContext:{risk:'low',complexity:'routine'},authorizationId:'synthetic-plan-0001'});assert.equal(prepared.route.planOnly,true);assert.equal(prepared.route.nonAuthorizing,true);assert.equal(prepared.route.ownerRequestedDeepSeek,false);
});
test('approval fields and reusable standing policy remain separate mandatory gates',async t=>{
 const data=await fixture(t),card=await prepareDecisionCard({root:data.root,task:data.implementation});
 const originalActions=process.env.GITHUB_ACTIONS,originalFetch=globalThis.fetch;
 const options={root:data.root,task:data.implementation,output:path.join(data.outside,'never.json')};
 let calls=0;
 globalThis.fetch=async()=>{calls++;throw new Error('must not transmit');};
 try {
   for(const [approvedCard,code] of [[card,'OWNER_TASK_REQUEST_REQUIRED'],[{...approve(card),transferApproved:false},'SOURCE_TRANSFER_AUTHORIZATION_REQUIRED'],[{...approve(card),paymentApproved:false},'PAID_CALL_AUTHORIZATION_REQUIRED']]) {
     await assert.rejects(executeDecisionCard({...options,approvedCard}),{code});
   }
   process.env.GITHUB_ACTIONS='true';
   await assert.rejects(executeDecisionCard({...options,approvedCard:approve(card)}),{code:'OPERATOR_ENVIRONMENT_MISMATCH'});
   delete process.env.GITHUB_ACTIONS;
   await assert.rejects(executeDecisionCard({...options,approvedCard:approve(card)}),{code:'POLICY_REVIEW_REQUIRED'});
   assert.equal(calls,0);
   await assert.rejects(access(options.output),{code:'ENOENT'});
 } finally {
   if(originalActions===undefined)delete process.env.GITHUB_ACTIONS;
   else process.env.GITHUB_ACTIONS=originalActions;
   globalThis.fetch=originalFetch;
 }
});
test('task, role, destination, inventory, body, request, caps and expired cards cannot be substituted',async t=>{
 const data=await fixture(t);const card=approve(await prepareDecisionCard({root:data.root,task:data.implementation}));let calls=0;const harness=createDeepSeekOperatorTestHarness({fetchImpl:async()=>{calls++;throw new Error('tampering must fail before transport');}});const options={root:data.root,task:data.implementation,standingPolicy:standing(),output:path.join(data.outside,'never.json')};
 for(const patch of [{destination:'https://example.com'},{inventory:[]},{bodySha256:'f'.repeat(64)},{requestSha256:'e'.repeat(64)},{maxCostUsd:.01},{applyChanges:true}])await assert.rejects(harness.executeDecisionCard({...options,approvedCard:{...card,...patch}}),{code:'OPERATOR_CARD_MISMATCH'});
 await assert.rejects(harness.executeDecisionCard({...options,approvedCard:{...card,role:'review'}}),{code:'OWNER_TASK_SCOPE_MISMATCH'});await assert.rejects(harness.executeDecisionCard({...options,approvedCard:{...card,expiresAt:new Date(Date.now()-1).toISOString()}}),{code:'OWNER_TASK_REQUEST_EXPIRED'});await assert.rejects(harness.executeDecisionCard({...options,task:{...data.implementation,taskId:'different-task'},approvedCard:card}),{code:'OWNER_TASK_SCOPE_MISMATCH'});await assert.rejects(harness.executeDecisionCard({...options,task:{...data.implementation,instruction:'A different task instruction.'},approvedCard:card}),{code:'OPERATOR_CARD_MISMATCH'});assert.equal(calls,0);
});
test('hosted ceilings, source eligibility and standing-policy tampering fail before transport',async t=>{
 const data=await fixture(t);await assert.rejects(prepareDecisionCard({root:data.root,task:{...data.implementation,executionEnvironment:'hosted',maxCostUsd:.51}}),{code:'OPERATOR_LIMIT_INVALID'});await assert.rejects(prepareDecisionCard({root:data.root,task:{...data.implementation,ownedPaths:['mobile/private/health.json']}}),{code:'PATH_NOT_ALLOWLISTED'});await assert.rejects(prepareDecisionCard({root:data.root,task:{...data.implementation,standingPolicy:standing()}}),{code:'OPERATOR_TASK_SCHEMA_INVALID'});
 const card=approve(await prepareDecisionCard({root:data.root,task:data.implementation}));let calls=0;const harness=createDeepSeekOperatorTestHarness({fetchImpl:async()=>{calls++;throw new Error('must not transmit');}});await assert.rejects(harness.executeDecisionCard({root:data.root,task:data.implementation,approvedCard:card,standingPolicy:{...standing(),sourcePolicyDigest:'f'.repeat(64)},output:path.join(data.outside,'never.json')}),{code:'SOURCE_ACTIVATION_INVALID'});assert.equal(calls,0);
});
test('stale exact source HEAD cannot consume a prior task card',async t=>{
 const data=await fixture(t),card=approve(await prepareDecisionCard({root:data.root,task:data.implementation}));await writeFile(path.join(data.root,'lib/source.mjs'),'export const value = 99;\n');data.git('add','.');data.git('commit','-qm','Later source');let calls=0;const harness=createDeepSeekOperatorTestHarness({fetchImpl:async()=>{calls++;}});await assert.rejects(harness.executeDecisionCard({root:data.root,task:data.implementation,approvedCard:card,standingPolicy:standing(),output:path.join(data.outside,'never.json')}),{code:'STALE_HEAD'});assert.equal(calls,0);
});
test('one approved implementation card uses the fixed stateful fake path and returns a test handoff',async t=>{
 const data=await fixture(t);const card=approve(await prepareDecisionCard({root:data.root,task:data.implementation}));const output=path.join(data.outside,'implementation.json');let calls=0;
 const harness=createDeepSeekOperatorTestHarness({fetchImpl:async(_url,options)=>{calls++;const durable=JSON.parse(await readFile(output,'utf8'));assert.equal(durable.status,'REQUEST_MAY_HAVE_BEEN_SENT');const body=JSON.parse(options.body);const source=JSON.parse(body.messages[1].content).sources[0];return new Response(JSON.stringify({model:'deepseek-v4-pro',id:'synthetic-implementation',usage:{prompt_tokens:10,completion_tokens:5,total_tokens:15},choices:[{finish_reason:'stop',message:{content:JSON.stringify({summary:'Prepared bounded source proposal.',changes:[{path:source.path,original_sha256:source.sha256,content:'export const value = 3;\n'}]})}}]}),{status:200});}});
 const result=await harness.executeDecisionCard({root:data.root,task:data.implementation,approvedCard:card,standingPolicy:standing(),output});assert.equal(calls,1);assert.equal(result.status,'PROPOSAL_READY');assert.equal(result.executionKind,'OFFLINE_TEST');assert.equal(result.tests[0].status,'NOT_RUN');assert.ok(result.tests[0].argv.includes('tests/focused.test.mjs'));assert.equal(await readFile(path.join(data.root,'lib/source.mjs'),'utf8'),'export const value = 2;\n');assert.ok(result.proposalArtifact);
});
test('explicit task/card-bound apply is bounded and still never runs generated test code',async t=>{
 const data=await fixture(t);const task={...data.implementation,applyChanges:true};const card=approve(await prepareDecisionCard({root:data.root,task}));const harness=createDeepSeekOperatorTestHarness({fetchImpl:async(_url,options)=>{const source=JSON.parse(JSON.parse(options.body).messages[1].content).sources[0];return new Response(JSON.stringify({model:'deepseek-v4-pro',usage:{prompt_tokens:10,completion_tokens:5,total_tokens:15},choices:[{finish_reason:'stop',message:{content:JSON.stringify({summary:'Bounded isolated application.',changes:[{path:source.path,original_sha256:source.sha256,content:'export const value = 3;\n'}]})}}]}),{status:200});}});const report=await harness.executeDecisionCard({root:data.root,task,approvedCard:card,standingPolicy:standing(),output:path.join(data.outside,'applied.json')});assert.equal(report.status,'APPLIED_UNTESTED');assert.equal(report.tests[0].status,'NOT_RUN');assert.equal(await readFile(path.join(data.root,'lib/source.mjs'),'utf8'),'export const value = 3;\n');
});
test('one approved reviewer card reserves and resumes exactly once through durable fake state',async t=>{
 const data=await fixture(t);const card=approve(await prepareDecisionCard({root:data.root,task:data.review,github:data.github}));const output=path.join(data.outside,'review.json');let calls=0;const harness=createDeepSeekOperatorTestHarness({github:data.github,fetchImpl:async()=>{calls++;return new Response(JSON.stringify({model:'deepseek-v4-pro',id:'synthetic-review',usage:{prompt_tokens:10,completion_tokens:5,total_tokens:15},choices:[{finish_reason:'stop',message:{content:JSON.stringify({schema_version:'mile-commons.deepseek-review-response.v1',summary:'Synthetic bounded protocol result.',findings:[]})}}]}),{status:200});}});const report=await harness.executeDecisionCard({root:data.root,task:data.review,approvedCard:card,standingPolicy:standing(),output});assert.equal(calls,1);assert.equal(report.request_status,'SUCCEEDED');assert.equal(report.execution_kind,'OFFLINE_TEST');assert.equal(report.independent_review_attested,false);const state=JSON.parse(await readFile(report.stateReceiptPath,'utf8'));assert.equal(state.provider_attempt_state,'REVIEW_COMPLETE');assert.equal(state.authorization_id,card.authorizationId);
});
test('operator records require private canonical files outside repository source',async t=>{
 const data=await fixture(t);const inside=path.join(data.root,'card.json');await writeFile(inside,'{}',{mode:0o600});await assert.rejects(readOperatorFile(inside,{root:data.root,approval:true}),{code:'OPERATOR_RECORD_MUST_BE_EXTERNAL'});await symlink(data.root,path.join(data.outside,'source-link'));await assert.rejects(readOperatorFile(path.join(data.outside,'source-link','card.json'),{root:data.root,approval:true}),{code:'OPERATOR_FILE_UNSAFE'});const publicFile=path.join(data.outside,'public.json');await writeFile(publicFile,'{}',{mode:0o644});await assert.rejects(readOperatorFile(publicFile,{root:data.root,approval:true}),{code:'OPERATOR_FILE_NOT_PRIVATE'});
});

test('the single prepare command writes a private non-authorizing card without credentials',async t=>{
 const data=await fixture(t);const taskFile=path.join(data.outside,'task.json'),cardFile=path.join(data.outside,'decision.json');await writeFile(taskFile,JSON.stringify(data.implementation),{mode:0o600});
 const script=new URL('../scripts/deepseek.mjs',import.meta.url).pathname;const result=JSON.parse(execFileSync(process.execPath,[script,'prepare','--root',data.root,'--task',taskFile,'--card',cardFile],{encoding:'utf8',stdio:['ignore','pipe','pipe']}));
 assert.equal(result.status,'PLAN_ONLY');assert.equal(result.providerCalls,0);const card=JSON.parse(await readFile(cardFile,'utf8'));assert.equal(card.ownerRequested,false);assert.equal(card.transferApproved,false);assert.equal(card.paymentApproved,false);assert.equal((await stat(cardFile)).mode&0o777,0o600);
});

test('advisory hosted cards cannot invoke the local combined path or expose a credential',async t=>{
 const data=await fixture(t);const task={...data.implementation,executionEnvironment:'hosted',maxCostUsd:.5};const card=approve(await prepareDecisionCard({root:data.root,task}));const oldActions=process.env.GITHUB_ACTIONS,oldFetch=globalThis.fetch;let fetches=0;const output=path.join(data.outside,'hosted-forbidden.json');
 process.env.GITHUB_ACTIONS='true';globalThis.fetch=async()=>{fetches++;throw new Error('hosted dispatch must stay separate');};
 try {await assert.rejects(executeDecisionCard({root:data.root,task,approvedCard:card,standingPolicy:standing(),output}),{code:'HOSTED_DISPATCH_REQUIRED'});assert.equal(fetches,0);await assert.rejects(access(output),{code:'ENOENT'});}finally{if(oldActions===undefined)delete process.env.GITHUB_ACTIONS;else process.env.GITHUB_ACTIONS=oldActions;globalThis.fetch=oldFetch;}
});
