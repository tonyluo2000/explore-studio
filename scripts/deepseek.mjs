#!/usr/bin/env node
import {createHash,randomUUID,randomInt} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {constants} from 'node:fs';
import {open,mkdir,lstat,realpath} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {planImplementation,executeImplementationWithReceipt,createDeepSeekImplementationTestHarness} from './deepseek-agent.mjs';
import {prepareReviewInput,buildMessages,prepareDeepSeekRequest,splitUnifiedDiff,makeIdempotencyKey,reviewTaskId,runReviewWithState,createDeepSeekReviewTestHarness,createDeepSeekTestClient,MIN_HIGH_REVIEW_OUTPUT_TOKENS} from './deepseek-review-core.mjs';
import {createGitHubClient} from './deepseek-review.mjs';
import {qualityRequirements,assertQualityFloor,isRoutineDeepSeekImplementation} from './model-quality.mjs';
import {assertOwnerTaskRequest,assertCallAuthorization} from './model-authorization.mjs';
import {assertSourceActivation,assertOrdinaryDeepSeekCall} from './model-activation.mjs';

export const TASK_SCHEMA='cross-project.deepseek-operator-task.v1';
export const CARD_SCHEMA='cross-project.deepseek-decision-card.v1';
const DESTINATION='https://api.deepseek.com/chat/completions';
const PROJECTS=new Set(['tonyluo2000/mile-commons','briersystems/montefinance','tonyluo2000/explore-studio']);
const fail=code=>{throw Object.assign(new Error(code),{code});};
const hash=value=>createHash('sha256').update(value).digest('hex');
const stable=value=>JSON.stringify(value,(_key,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.keys(item).sort().map(key=>[key,item[key]])):item);
const git=(root,args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8',stdio:['ignore','pipe','pipe'],maxBuffer:2000000}).trim();
const plain=value=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.getPrototypeOf(value)===Object.prototype;
function keys(value,allowed,code) {if(!plain(value)||Object.keys(value).some(key=>!allowed.includes(key)))fail(code);}
const TASK_KEYS=['schema','repository','taskId','role','baseSha','headSha','taskType','risk','complexity','history','implementerFamily','title','instruction','ownedPaths','contextPaths','tests','pullNumber','reasoningEffort','maxCostUsd','maxOutputTokens','maxRequestBytes','maxDiffChars','applyChanges','executionEnvironment'];
function normalizeTask(task,standing=false) {
  keys(task,standing?[...TASK_KEYS,'model']:TASK_KEYS,'OPERATOR_TASK_SCHEMA_INVALID');
  if(task.schema!==TASK_SCHEMA||!PROJECTS.has(task.repository)||!['implementation','review'].includes(task.role)||! /^[a-z0-9][a-z0-9-]{0,63}$/.test(task.taskId??'')||!['baseSha','headSha'].every(key=>/^[a-f0-9]{40}$/.test(task[key]??'')))fail('OPERATOR_TASK_SCOPE_INVALID');
  const value={...task,taskType:task.taskType??(task.role==='review'?'review':'implementation'),risk:task.risk??'high',complexity:task.complexity??'standard',history:task.history??{},executionEnvironment:task.executionEnvironment??'local',applyChanges:task.applyChanges??false,maxCostUsd:task.maxCostUsd??.15,maxOutputTokens:task.maxOutputTokens??4000,maxRequestBytes:task.maxRequestBytes??(task.role==='review'?160000:64000),maxDiffChars:task.maxDiffChars??120000};
  if(!Number.isSafeInteger(value.maxDiffChars)||value.maxDiffChars<1||value.maxDiffChars>120000||!['local','hosted'].includes(value.executionEnvironment)||typeof value.applyChanges!=='boolean'||!Number.isFinite(value.maxCostUsd)||value.maxCostUsd<=0||value.maxCostUsd>(value.executionEnvironment==='hosted'?.5:1))fail('OPERATOR_LIMIT_INVALID');
  if(value.role==='review'&&(value.taskId!==reviewTaskId(value.pullNumber)||!Number.isSafeInteger(value.pullNumber)||value.pullNumber<1||value.taskType!=='review'||value.applyChanges||!['openai','claude'].includes(value.implementerFamily)))fail('OPERATOR_REVIEW_SCOPE_INVALID');
  const quality=qualityRequirements(value);const effort=value.reasoningEffort??(quality.minimumEffort==='low'?'low':'high');
  if(!['low','high'].includes(effort))fail('INVALID_DEEPSEEK_EFFORT');assertQualityFloor({requestedEffort:effort,requirements:quality});
  if(value.role==='review'&&effort==='high'&&value.maxOutputTokens<MIN_HIGH_REVIEW_OUTPUT_TOKENS)fail('HIGH_REVIEW_OUTPUT_ENVELOPE_REQUIRED');
  const routine=isRoutineDeepSeekImplementation({...value,risk:quality.risk,reasoningEffort:effort});
  if(task.model!==undefined && task.model!=='deepseek-v4-pro' && !(task.model==='deepseek-flash' && routine))fail('OPERATOR_MODEL_NOT_ALLOWED');
  const model=task.model??(routine?'deepseek-flash':'deepseek-v4-pro');
  return {...value,reasoningEffort:effort,...(standing?{model}:{})};
}
async function repositoryRoot(root,task) {
  root=path.resolve(root);if(await realpath(root)!==root)fail('NONCANONICAL_PROJECT_ROOT');
  const remote=git(root,['remote','get-url','origin']).replace(/\.git$/,'');
  if(![`https://github.com/${task.repository}`,`git@github.com:${task.repository}`].includes(remote))fail('REPOSITORY_IDENTITY_MISMATCH');
  if(git(root,['rev-parse','HEAD'])!==task.headSha)fail('STALE_HEAD');git(root,['merge-base','--is-ancestor',task.baseSha,task.headSha]);return root;
}
function manifestFor(task) {
  return {schema:'cross-project.deepseek-implementation.v1',repository:task.repository,taskId:task.taskId,taskType:task.taskType,title:task.title,instruction:task.instruction,baseSha:task.baseSha,headSha:task.headSha,ownedPaths:task.ownedPaths,contextPaths:task.contextPaths??[],tests:task.tests??[],...(task.pullNumber===undefined?{}:{pullNumber:task.pullNumber}),model:task.model??'deepseek-v4-pro',maxCostUsd:task.maxCostUsd,maxOutputTokens:task.maxOutputTokens,maxRequestBytes:task.maxRequestBytes};
}
const contextFor=task=>({risk:task.risk,complexity:task.complexity,history:task.history,implementerFamily:task.implementerFamily,overrides:{reasoningEffort:task.reasoningEffort}});
const scopeFor=task=>Object.fromEntries(['repository','taskId','role','baseSha','headSha'].map(key=>[key,task[key]]));
async function prepareSource({root,task,authorizationId,github}) {
  if(task.role==='implementation') {
    const prepared=await planImplementation({root,manifest:manifestFor(task),routingContext:contextFor(task),authorizationId,reasoningEffort:task.reasoningEffort});
    return {requestId:prepared.requestId,bodySha256:hash(prepared.request.serializedBody),inventory:prepared.sources.map(source=>({path:source.path,sha256:source.sha256,owned:source.owned})).sort((a,b)=>a.path.localeCompare(b.path)),request:prepared.request};
  }
  const pull=await github.getPull(task.repository,task.pullNumber);
  const assertPull=value=>{if(value?.state!=='open'||value.head?.sha!==task.headSha||value.base?.sha!==task.baseSha)fail('STALE_REVIEW_SCOPE');};assertPull(pull);
  const snapshot=await github.getComparison(task.repository,task.baseSha,task.headSha);
  if(snapshot?.complete!==true||snapshot.baseSha!==task.baseSha||snapshot.headSha!==task.headSha||!Number.isSafeInteger(snapshot.totalCommits)||snapshot.totalCommits<1||!/^[a-f0-9]{40}$/.test(snapshot.mergeBaseSha??''))fail('COMPARISON_INCOMPLETE');
  const prepared=prepareReviewInput({repository:task.repository,diff:snapshot.diff,files:snapshot.files,maxDiffChars:task.maxDiffChars,classificationContext:{root,baseSha:task.baseSha,headSha:task.headSha}});
  const built=buildMessages({repository:task.repository,pullNumber:task.pullNumber,baseSha:task.baseSha,headSha:task.headSha,title:pull.title,body:pull.body,prepared});
  const request=prepareDeepSeekRequest({model:'deepseek-v4-pro',messages:built.messages,reasoningEffort:task.reasoningEffort,maxCostUsd:task.maxCostUsd,maxOutputTokens:task.maxOutputTokens,maxRequestBytes:task.maxRequestBytes,retries:0});
  const requestId=makeIdempotencyKey({...task,model:'deepseek-v4-pro',mode:'live',authorizationId,providerRetries:0});
  const sections=new Map(splitUnifiedDiff(snapshot.diff).map(section=>[section.filename,section.text]));
  const inventory=snapshot.files.map(file=>({path:file.filename,sha256:hash(sections.get(file.filename)),additions:file.additions,deletions:file.deletions})).sort((a,b)=>a.path.localeCompare(b.path));
  assertPull(await github.getPull(task.repository,task.pullNumber));return {requestId,bodySha256:hash(request.serializedBody),inventory,request};
}
const immutableCard=(task,prepared,authorizationId)=>({schema:CARD_SCHEMA,...scopeFor(task),provider:'deepseek',model:task.model??'deepseek-v4-pro',effectiveEffort:task.reasoningEffort,destination:DESTINATION,executionEnvironment:task.executionEnvironment,inventory:prepared.inventory,taskSha256:hash(stable(task)),requestSha256:prepared.requestId,bodySha256:prepared.bodySha256,maxCostUsd:task.maxCostUsd,maxOutputTokens:task.maxOutputTokens,maxRequestBytes:task.maxRequestBytes,maxDiffChars:task.maxDiffChars,weeklyMaximumUsd:10,allocationMaximumUsd:5,budgetWindowHours:168,automaticRetries:0,applyChanges:task.applyChanges,testExecution:'HANDOFF_ONLY',authorizationId});
export async function prepareDecisionCard({root=process.cwd(),task,github=createGitHubClient()}={}) {
  task=normalizeTask(task);root=await repositoryRoot(root,task);const authorizationId='decision-'+randomUUID();
  const prepared=await prepareSource({root,task,authorizationId,github});const now=Date.now();
  return {...immutableCard(task,prepared,authorizationId),issuedAt:new Date(now).toISOString(),expiresAt:new Date(now+3600000).toISOString(),authorizationReference:'pending-owner-decision',ownerRequested:false,transferApproved:false,paymentApproved:false};
}
function grants(card) {
  const ownerRequest={schema:'cross-project.deepseek-owner-request.v1',...scopeFor(card),model:card.model,authorizationId:card.authorizationId,issuedAt:card.issuedAt,expiresAt:card.expiresAt,authorizationReference:card.authorizationReference};
  const callAuthorization={...ownerRequest,schema:'cross-project.deepseek-call-authorization.v1',requestId:card.requestSha256,bodySha256:card.bodySha256,reasoningEffort:card.effectiveEffort,maxCostUsd:card.maxCostUsd,transferApproved:card.transferApproved,paymentApproved:card.paymentApproved};return {ownerRequest,callAuthorization};
}
async function outputFile(filename,root) {
  if(typeof filename!=='string'||!path.isAbsolute(filename))fail('ABSOLUTE_EXTERNAL_OUTPUT_REQUIRED');filename=path.resolve(filename);
  if(filename===root||filename.startsWith(root+path.sep))fail('OPERATOR_RECORD_MUST_BE_EXTERNAL');
  let current=path.parse(filename).root;for(const part of path.dirname(filename).slice(current.length).split(path.sep).filter(Boolean)){current=path.join(current,part);try{await mkdir(current,{mode:0o700});}catch(error){if(error.code!=='EEXIST')throw error;}const stat=await lstat(current);if(!stat.isDirectory()||stat.isSymbolicLink())fail('OPERATOR_OUTPUT_UNSAFE');}
  return open(filename,constants.O_RDWR|constants.O_CREAT|constants.O_EXCL|constants.O_NOFOLLOW,0o600);
}
const productionRuntime={implementation:executeImplementationWithReceipt,review:runReviewWithState,github:createGitHubClient,offline:false};
async function executeTask({root=process.cwd(),task,approvedCard,standingPolicy,output},runtime,ordinary=false) {
  task=normalizeTask(task,ordinary);
  if(!runtime.offline&&task.executionEnvironment==='hosted')fail('HOSTED_DISPATCH_REQUIRED');
  root=await repositoryRoot(root,task);
  if(!runtime.offline&&((process.env.GITHUB_ACTIONS==='true')!==(task.executionEnvironment==='hosted')))fail('OPERATOR_ENVIRONMENT_MISMATCH');
  let card=approvedCard;
  if(!ordinary) {
    if(!plain(card)||card.schema!==CARD_SCHEMA||card.ownerRequested!==true)fail('OWNER_TASK_REQUEST_REQUIRED');
    if(card.transferApproved!==true)fail('SOURCE_TRANSFER_AUTHORIZATION_REQUIRED');
    if(card.paymentApproved!==true)fail('PAID_CALL_AUTHORIZATION_REQUIRED');
    if(card.authorizationReference==='pending-owner-decision')fail('OWNER_TASK_REQUEST_REQUIRED');
    assertOwnerTaskRequest({request:grants(card).ownerRequest,scope:scopeFor(task)});
  }
  if(!ordinary)assertSourceActivation({activation:standingPolicy,repository:task.repository});
  const authorizationId=ordinary?'standing-'+randomUUID():card.authorizationId;
  const github=runtime.github();
  const prepared=await prepareSource({root,task,authorizationId,github});
  const expected=immutableCard(task,prepared,authorizationId);
  if(ordinary) {
    assertOrdinaryDeepSeekCall({activation:standingPolicy,repository:task.repository,task,files:prepared.inventory.map(source=>source.path),maxCostUsd:task.maxCostUsd});
    const now=Date.now();
    card={...expected,issuedAt:new Date(now).toISOString(),expiresAt:new Date(now+3600000).toISOString(),authorizationReference:standingPolicy.ownerApprovalReference,ownerRequested:true,transferApproved:true,paymentApproved:true};
  } else {
    keys(card,[...Object.keys(expected),'issuedAt','expiresAt','authorizationReference','ownerRequested','transferApproved','paymentApproved'],'OPERATOR_CARD_SCHEMA_INVALID');
    if(Object.keys(expected).some(key=>stable(card[key])!==stable(expected[key])))fail('OPERATOR_CARD_MISMATCH');
  }
  const {ownerRequest,callAuthorization}=grants(card);
  assertCallAuthorization({authorization:callAuthorization,ownerRequest,scope:scopeFor(task),requestId:prepared.requestId,bodySha256:prepared.bodySha256,reasoningEffort:task.reasoningEffort,maxCostUsd:task.maxCostUsd});
  if(task.role==='implementation')return runtime.implementation({root,manifest:manifestFor(task),ownerRequest,approval:callAuthorization,activation:standingPolicy,routingContext:contextFor(task),mode:'live',apply:task.applyChanges,output});
  const handle=await outputFile(output,root);const stateDirectory=output+'.state';
  let report={schema:'cross-project.deepseek-operator-result.v1',status:'STATEFUL_REVIEW_PREPARED',requestId:prepared.requestId,authorizationId:card.authorizationId,stateDirectory,providerCallStatus:'NOT_SENT',testExecution:'HANDOFF_ONLY'};
  const persist=async()=>{await handle.truncate(0);await handle.write(JSON.stringify(report,null,2)+'\n',0,'utf8');await handle.sync();};
  try {
    await persist();const reservationId=`${Date.now()}-${randomInt(1,1000000)}`;
    const reviewOptions={repository:task.repository,pullNumber:task.pullNumber,baseSha:task.baseSha,headSha:task.headSha,model:'deepseek-v4-pro',reasoningEffort:task.reasoningEffort,mode:'live',acknowledgeExternalTransfer:true,ownerRequest,callAuthorization,activation:standingPolicy,sourceRoot:root,routingContext:contextFor(task),github,maxCostUsd:task.maxCostUsd,maxOutputTokens:task.maxOutputTokens,maxRequestBytes:task.maxRequestBytes,maxDiffChars:task.maxDiffChars,providerRetries:0};
    const reserved=await runtime.review({stateDirectory,reviewOptions:{...reviewOptions,reserveOnly:true,reservationId}});
    if(reserved.report.request_status!=='RESERVED')report={...reserved.report,stateReceiptPath:reserved.receiptPath};
    else {const completed=await runtime.review({stateDirectory,reviewOptions:{...reviewOptions,apiKey:runtime.offline?'offline-test-key':process.env.DEEPSEEK_API_KEY,resumeReservationId:reservationId}});report={...completed.report,stateReceiptPath:completed.receiptPath};}
    return report;
  } finally {try{await persist();}finally{await handle.close();}}
}
export const executeDecisionCard=options=>executeTask(options,productionRuntime);
const executeStandingTask=options=>executeTask(options,productionRuntime,true);
export function createDeepSeekOperatorTestHarness({fetchImpl,github}={}) {
  const assertTest=()=>{if(process.env.NODE_TEST_CONTEXT!=='child-v8'||typeof fetchImpl!=='function'||fetchImpl===fetch)fail('TEST_OPERATOR_CONTEXT_REQUIRED');};assertTest();
  const implementation=createDeepSeekImplementationTestHarness({fetchImpl});const client=createDeepSeekTestClient({fetchImpl});const review=createDeepSeekReviewTestHarness({providerCall:options=>client(options)});
  const runtime={implementation:options=>{assertTest();return implementation.executeImplementationWithReceipt(options);},review:options=>{assertTest();return review.runReviewWithState(options);},github:()=>github??createGitHubClient(),offline:true};
  return {
    executeDecisionCard:options=>{assertTest();return executeTask(options,runtime);},
    executeStandingTask:options=>{assertTest();return executeTask(options,runtime,true);}
  };
}
export async function readOperatorFile(filename,{root,approval=false}={}) {
  filename=path.resolve(filename);if(await realpath(filename)!==filename)fail('OPERATOR_FILE_UNSAFE');if(approval&&(filename===root||filename.startsWith(root+path.sep)))fail('OPERATOR_RECORD_MUST_BE_EXTERNAL');
  const handle=await open(filename,constants.O_RDONLY|constants.O_NOFOLLOW);try{const stat=await handle.stat();if(!stat.isFile()||stat.size>256000)fail('OPERATOR_FILE_INVALID');if(approval&&((stat.mode&0o077)!==0||typeof process.geteuid==='function'&&stat.uid!==process.geteuid()))fail('OPERATOR_FILE_NOT_PRIVATE');return JSON.parse(await handle.readFile('utf8'));}finally{await handle.close();}
}
export async function main(argv) {
  if(argv.includes('--help')){
    console.log('deepseek run --task /external/TASK --output /external/REPORT [--standing-policy /external/POLICY] [--root ROOT]\n'+
      'Set DEEPSEEK_STANDING_POLICY_FILE once to use the approved policy. Prepare/execute remain available for separately authorized tasks. Focused tests are handed off to Codex.');
    return 0;
  }
  const command=argv.shift();
  if(!['prepare','execute','run'].includes(command))fail('OPERATOR_COMMAND_REQUIRED');
  const args={};
  while(argv.length){const key=argv.shift();if(!['--task','--card','--standing-policy','--output','--root'].includes(key)||!argv[0]||argv[0].startsWith('--')||args[key])fail('OPERATOR_ARGUMENT_INVALID');args[key]=argv.shift();}
  const root=await realpath(path.resolve(args['--root']??process.cwd()));
  if(!args['--task'] || (command==='run' ? args['--card'] : !args['--card']))fail('OPERATOR_ARGUMENT_INVALID');
  const task=await readOperatorFile(args['--task'],{root,approval:command==='run'});
  if(command==='prepare'){const card=await prepareDecisionCard({root,task});const handle=await outputFile(args['--card'],root);try{await handle.writeFile(JSON.stringify(card,null,2)+'\n');await handle.sync();}finally{await handle.close();}console.log(JSON.stringify({status:'PLAN_ONLY',card:path.resolve(args['--card']),providerCalls:0}));return 0;}
  const policyPath=args['--standing-policy']??process.env.DEEPSEEK_STANDING_POLICY_FILE;
  if(!policyPath||!args['--output'])fail('OPERATOR_ARGUMENT_INVALID');
  const standingPolicy=await readOperatorFile(policyPath,{root,approval:true});
  const options={root,task,standingPolicy,output:args['--output']};
  const report=command==='run' ? await executeStandingTask(options) :
    await executeDecisionCard({...options,approvedCard:await readOperatorFile(args['--card'],{root,approval:true})});
  console.log(JSON.stringify({status:report.status??report.request_status,report:args['--output']}));
  return ['PROPOSAL_READY','APPLIED_UNTESTED','SUCCEEDED'].includes(report.status??report.request_status)?0:1;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main(process.argv.slice(2)).then(code=>{process.exitCode=code;}).catch(error=>{console.error(`deepseek: ${/^[A-Z0-9_]+$/.test(error.code??'')?error.code:'OPERATOR_FAILED'}`);process.exitCode=1;});
