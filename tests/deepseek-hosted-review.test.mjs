import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdtemp,realpath,rm,mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {prepareHostedReview,validateHostedRequest} from '../scripts/deepseek-hosted-review.mjs';
import {assertCallAuthorization} from '../scripts/model-authorization.mjs';

async function fixture(t) {
  const root=await realpath(await mkdtemp(path.join(os.tmpdir(),'deepseek-hosted-source-')));t.after(()=>rm(root,{recursive:true,force:true}));
  const git=(...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
  git('init','--quiet');git('config','user.name','Synthetic Test');git('config','user.email','test@example.org');
  git('remote','add','origin','https://github.com/tonyluo2000/mile-commons.git');
  await mkdir(path.join(root,'scripts'));await writeFile(path.join(root,'scripts/sample.mjs'),'export const value = 1;\n');
  git('add','.');git('commit','--quiet','-m','base');const baseSha=git('rev-parse','HEAD');
  await writeFile(path.join(root,'scripts/sample.mjs'),'export const value = 2;\n');git('add','.');git('commit','--quiet','-m','head');const headSha=git('rev-parse','HEAD');
  const request={schema:'cross-project.hosted-review-request.v1',repository:'tonyluo2000/mile-commons',pr:1,baseSha,headSha,risk:'low',implementerFamily:'openai',reasoningEffort:'low',maxCostUsd:.3};
  const env={GITHUB_REPOSITORY:request.repository,GITHUB_ACTOR:'tonyluo2000',GITHUB_EVENT_NAME:'workflow_dispatch',GITHUB_RUN_ATTEMPT:'1',GITHUB_RUN_ID:'42',GITHUB_SHA:headSha,GITHUB_WORKFLOW_SHA:headSha};
  const pull={state:'open',title:'Synthetic tooling change',body:'Source only.',base:{sha:baseSha},head:{sha:headSha}};
  const snapshot={complete:true,baseSha,headSha,mergeBaseSha:baseSha,status:'ahead',totalCommits:1,
    files:[{filename:'scripts/sample.mjs',additions:1,deletions:1}],diff:git('diff',baseSha,headSha)+'\n'};
  return {request,env,sourceRoot:root,github:{getPull:async()=>pull,getComparison:async()=>snapshot}};
}
test('mock preview returns one complete decision card and never grants payment',async t=>{
  const f=await fixture(t);const result=await prepareHostedReview({...f,mode:'mock'});
  assert.equal(result.card.model,'deepseek-v4-pro');assert.equal(result.card.reasoningEffort,'low');
  assert.deepEqual(result.card.files,['scripts/sample.mjs']);assert.equal(result.card.providerCalls,0);
  assert.equal(result.approval,undefined);assert.equal(result.report.request_status,'MOCK_ONLY');
});
test('live owner dispatch binds one exact body grant to the current run identity',async t=>{
  const f=await fixture(t);const preview=await prepareHostedReview({...f,mode:'mock'});
  f.request.sourceBodySha256=preview.card.sourceBodySha256;
  f.request.activation={independentReview:{headSha:f.env.GITHUB_SHA}};
  f.env.DEEPSEEK_EXPLICIT_APPROVAL='APPROVE DEEPSEEK REQUEST';
  const result=await prepareHostedReview({...f,mode:'live'});
  const scope={repository:f.request.repository,taskId:'pr-1-review',role:'review',baseSha:f.request.baseSha,headSha:f.request.headSha};
  assert.equal(result.approval.authorizationId,'gh-run-42');
  assertCallAuthorization({authorization:result.approval,ownerRequest:result.ownerRequest,scope,
    requestId:result.approval.requestId,bodySha256:preview.card.sourceBodySha256,reasoningEffort:'low',maxCostUsd:.3});
  // This adapter only prepares documents; production activation is separately
  // validated by the fixed review transport before a paid reservation.
  assert.equal(result.card.providerCalls,0);
});
test('a changed body, missing explicit approval, or unreviewed control head refuses',async t=>{
  const f=await fixture(t);f.request.sourceBodySha256='a'.repeat(64);f.request.activation={independentReview:{headSha:f.env.GITHUB_SHA}};
  await assert.rejects(prepareHostedReview({...f,mode:'live'}),{code:'EXACT_HOSTED_SOURCE_PAYMENT_APPROVAL_REQUIRED'});
  f.env.DEEPSEEK_EXPLICIT_APPROVAL='APPROVE DEEPSEEK REQUEST';
  await assert.rejects(prepareHostedReview({...f,mode:'live'}),{code:'EXACT_HOSTED_SOURCE_PAYMENT_APPROVAL_REQUIRED'});
  const preview=await prepareHostedReview({...f,mode:'mock'});f.request.sourceBodySha256=preview.card.sourceBodySha256;
  f.request.activation.independentReview.headSha='b'.repeat(40);
  await assert.rejects(prepareHostedReview({...f,mode:'live'}),{code:'HOSTED_CONTROL_NOT_REVIEWED'});
});
test('routine/high are explicit, while medium, excess cost and arbitrary repositories refuse',async t=>{
  const f=await fixture(t);
  for(const patch of [{reasoningEffort:'medium'},{maxCostUsd:.51},{repository:'outside/project'},{model:'different-model'}])
    assert.throws(()=>validateHostedRequest({...f.request,...patch}),{code:'HOSTED_REQUEST_INVALID'});
  f.request.reasoningEffort='high';f.request.risk='high';const p=await prepareHostedReview({...f,mode:'mock'});
  assert.equal(p.card.outputTokenCeiling,16000);assert.equal(p.card.reasoningEffort,'high');
});
test('non-owner and rerun contexts cannot prepare live authorization',async t=>{
  const f=await fixture(t);
  for(const patch of [{GITHUB_ACTOR:'another-user'},{GITHUB_RUN_ATTEMPT:'2'},{GITHUB_EVENT_NAME:'pull_request'}])
    await assert.rejects(prepareHostedReview({...f,env:{...f.env,...patch},mode:'mock'}),{code:'HOSTED_OWNER_DISPATCH_REQUIRED'});
});
