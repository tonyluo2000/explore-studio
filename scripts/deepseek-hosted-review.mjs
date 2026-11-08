#!/usr/bin/env node
// Adapter for the existing owner-dispatched workflow. No provider transport here.
import {readFile,writeFile,mkdir,appendFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {runReview,makeIdempotencyKey} from './deepseek-review-core.mjs';
import {createGitHubClient} from './deepseek-review.mjs';

const PROJECTS = new Set(['tonyluo2000/mile-commons','briersystems/montefinance','tonyluo2000/explore-studio']);
const fail = code => {throw Object.assign(new Error(code),{code});};
export function validateHostedRequest(request) {
  const keys=['schema','repository','pr','baseSha','headSha','risk','implementerFamily','reasoningEffort','maxCostUsd','sourceBodySha256','activation'];
  if (!request || request.schema !== 'cross-project.hosted-review-request.v1' || Object.keys(request).some(key=>!keys.includes(key))
    || !PROJECTS.has(request.repository) || !Number.isSafeInteger(request.pr) || request.pr<1
    || !/^[a-f0-9]{40}$/.test(request.baseSha??'') || !/^[a-f0-9]{40}$/.test(request.headSha??'')
    || !['low','high','critical'].includes(request.risk) || !['openai','claude','deepseek'].includes(request.implementerFamily)
    || request.reasoningEffort!==(request.risk==='low'?'low':'high') || !Number.isFinite(request.maxCostUsd)
    || request.maxCostUsd<=0 || request.maxCostUsd>.5
    || request.sourceBodySha256!==undefined && !/^[a-f0-9]{64}$/.test(request.sourceBodySha256)) fail('HOSTED_REQUEST_INVALID');
  return request;
}

export async function prepareHostedReview({request,mode,env=process.env,github,sourceRoot,now=Date.now()}) {
  validateHostedRequest(request);
  if (!['mock','live'].includes(mode) || env.GITHUB_REPOSITORY!=='tonyluo2000/mile-commons'
    || env.GITHUB_ACTOR!=='tonyluo2000' || env.GITHUB_EVENT_NAME!=='workflow_dispatch'
    || env.GITHUB_RUN_ATTEMPT!=='1' || !/^\d+$/.test(env.GITHUB_RUN_ID??'')) fail('HOSTED_OWNER_DISPATCH_REQUIRED');
  const authorizationId=`gh-run-${env.GITHUB_RUN_ID}`;
  const scope={repository:request.repository,taskId:`pr-${request.pr}-review`,role:'review',baseSha:request.baseSha,headSha:request.headSha};
  const ownerRequest={schema:'cross-project.deepseek-owner-request.v1',authorizationId,...scope,model:'deepseek-v4-pro',
    issuedAt:new Date(now-1000).toISOString(),expiresAt:new Date(now+30*60*1000).toISOString(),
    authorizationReference:`github:tonyluo2000/mile-commons/actions/runs/${env.GITHUB_RUN_ID}`};
  const options={repository:request.repository,pullNumber:request.pr,baseSha:request.baseSha,headSha:request.headSha,
    model:'deepseek-v4-pro',reasoningEffort:request.reasoningEffort,maxCostUsd:request.maxCostUsd,
    maxDiffChars:320000,maxRequestBytes:320000,maxOutputTokens:request.reasoningEffort==='high'?16000:4000,providerRetries:0,
    ownerRequest,sourceRoot,github,mode:'mock',routingContext:{risk:request.risk,implementerFamily:request.implementerFamily,complexity:request.risk==='low'?'routine':'complex'}};
  const report=await runReview(options);
  if (report.request_status!=='MOCK_ONLY' || !report.coverage.complete || report.errors.length)
    throw Object.assign(new Error('HOSTED_SOURCE_NOT_ELIGIBLE: '+report.errors.map(error=>error.code).join(',')),{code:'HOSTED_SOURCE_NOT_ELIGIBLE'});
  const card={schema:'cross-project.deepseek-decision.v1',repository:request.repository,pr:request.pr,
    baseSha:request.baseSha,headSha:request.headSha,role:'review',destination:'https://api.deepseek.com/chat/completions',
    model:'deepseek-v4-pro',risk:request.risk,implementerFamily:request.implementerFamily,reasoningEffort:request.reasoningEffort,files:report.coverage.files,
    redactions:report.coverage.redactions,classifications:report.coverage.classifications,
    sourceBodySha256:report.request_body_sha256,maximumCostUsd:request.maxCostUsd,outputTokenCeiling:options.maxOutputTokens,
    retries:0,providerCalls:0,gateEffect:'NONE',consent:'NOT_GRANTED_BY_PREVIEW'};
  let approval;
  if(mode==='live') {
    if(env.DEEPSEEK_EXPLICIT_APPROVAL!=='APPROVE DEEPSEEK REQUEST' || !sourceRoot
      || request.sourceBodySha256!==report.request_body_sha256) fail('EXACT_HOSTED_SOURCE_PAYMENT_APPROVAL_REQUIRED');
    const control=request.activation?.independentReview?.headSha;
    if(!/^[a-f0-9]{40}$/.test(control??'') || control!==env.GITHUB_SHA || control!==env.GITHUB_WORKFLOW_SHA) fail('HOSTED_CONTROL_NOT_REVIEWED');
    approval={schema:'cross-project.deepseek-call-authorization.v1',authorizationId,...scope,model:'deepseek-v4-pro',
      requestId:makeIdempotencyKey({...options,mode:'live',authorizationId}),bodySha256:report.request_body_sha256,
      reasoningEffort:request.reasoningEffort,maxCostUsd:request.maxCostUsd,transferApproved:true,paymentApproved:true,
      issuedAt:ownerRequest.issuedAt,expiresAt:ownerRequest.expiresAt,authorizationReference:ownerRequest.authorizationReference};
  }
  return {ownerRequest,approval,activation:request.activation,card,report,options};
}

async function fetchSource(request,root) {
  await mkdir(root,{recursive:false,mode:0o700});
  const sourceEnv={...process.env,GIT_TERMINAL_PROMPT:'0',GIT_CONFIG_COUNT:'0'};
  if(request.repository!=='tonyluo2000/explore-studio') Object.assign(sourceEnv,{GIT_CONFIG_COUNT:'1',GIT_CONFIG_KEY_0:'http.https://github.com/.extraheader',
    GIT_CONFIG_VALUE_0:`AUTHORIZATION: basic ${Buffer.from(`x-access-token:${process.env.GH_TOKEN}`).toString('base64')}`});
  const run=args=>execFileSync('git',['-C',root,...args],{stdio:['ignore','pipe','pipe'],timeout:120000,maxBuffer:2000000,
    env:sourceEnv});
  try {
    run(['init','--quiet']);run(['remote','add','origin',`https://github.com/${request.repository}.git`]);
    run(['fetch','--quiet','--no-tags','origin',request.baseSha,request.headSha]);
  } catch {fail('HOSTED_SOURCE_UNAVAILABLE');}
}

export async function main() {
  const raw=process.env.DEEPSEEK_REQUEST_JSON??'';
  if(Buffer.byteLength(raw)>20000) fail('HOSTED_REQUEST_TOO_LARGE');
  let request;try {request=JSON.parse(raw);}catch {fail('HOSTED_REQUEST_INVALID');}
  validateHostedRequest(request);
  const mode=process.env.REVIEW_MODE;
  if(!['mock','live'].includes(mode) || process.env.GITHUB_REPOSITORY!=='tonyluo2000/mile-commons'
    || process.env.GITHUB_ACTOR!=='tonyluo2000' || process.env.GITHUB_EVENT_NAME!=='workflow_dispatch'
    || process.env.GITHUB_RUN_ATTEMPT!=='1' || !/^\d+$/.test(process.env.GITHUB_RUN_ID??'')) fail('HOSTED_OWNER_DISPATCH_REQUIRED');
  const root=path.join(process.env.RUNNER_TEMP,'deepseek-source');
  await fetchSource(request,root);
  const github=createGitHubClient({token:request.repository==='tonyluo2000/explore-studio'?'':process.env.GH_TOKEN});
  const prepared=await prepareHostedReview({request,mode,sourceRoot:root,github});
  const files=path.join(process.env.RUNNER_TEMP,'deepseek-operator');await mkdir(files,{mode:0o700});
  for(const [name,value] of Object.entries({owner:prepared.ownerRequest,approval:prepared.approval,activation:prepared.activation,routing:prepared.options.routingContext,request})) {
    if(value!==undefined) await writeFile(path.join(files,name+'.json'),JSON.stringify(value)+'\n',{mode:0o600});
  }
  await mkdir('outputs/deepseek-review',{recursive:true});
  await writeFile('outputs/deepseek-review/decision.json',JSON.stringify(prepared.card,null,2)+'\n');
  await writeFile('outputs/deepseek-review/preflight.json',JSON.stringify(prepared.report,null,2)+'\n');
  const outputs={source_root:root,operator_dir:files,repository:request.repository,pr:request.pr,base:request.baseSha,head:request.headSha,
    effort:request.reasoningEffort,max_cost:request.maxCostUsd,max_output:prepared.options.maxOutputTokens};
  for(const [key,value] of Object.entries(outputs)) await appendFile(process.env.GITHUB_OUTPUT,`${key}=${value}\n`);
  if(mode==='live') await appendFile(process.env.GITHUB_ENV,`DEEPSEEK_REVIEWED_CONTROL_SHA=${request.activation.independentReview.headSha}\n`);
  console.log(`Hosted ${mode} source check complete; ${prepared.card.files.length} files; provider calls: 0.`);
}
if(process.argv[1] && import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch(error=>{console.error(error.code??'HOSTED_REVIEW_PREPARATION_FAILED');process.exitCode=1;});
}
