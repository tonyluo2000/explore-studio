#!/usr/bin/env node
import { execFileSync, spawn } from 'node:child_process';
import { readFile, lstat, realpath } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { resolveRoute } from './deepseek-routing.mjs';
import { discoverCapabilities } from './model-capabilities.mjs';
import { collectCodexQuota } from './model-quota.mjs';
import { decisionRecord, appendDecisionRecord } from './model-telemetry.mjs';
import { containsRecognizedSecret, containsSuspiciousHighEntropy } from './deepseek-source-scanner.mjs';

const fail = code => { throw Object.assign(new Error(code), { code }); };
const git = (root, args) => execFileSync('git', ['-C',root,...args], {encoding:'utf8',stdio:['ignore','pipe','pipe'],maxBuffer:100000}).trim();
const PILOT_PROMPT = 'Format this synthetic Markdown heading: #router pilot. Reply with exactly # Router pilot and nothing else. Do not use tools, read files, or access the network.';

export async function readInput(filename) {
  const stat = await lstat(filename);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 64000) fail('INVALID_INPUT_FILE');
  return JSON.parse(await readFile(filename,'utf8'));
}

export function primaryCommand(route, { root, pilot=false }={}) {
  if (route.provider === 'openai') return {
    command:'codex', args:['exec','--model',route.model,'-c',`model_reasoning_effort="${route.effectiveEffort}"`,'--sandbox',pilot?'read-only':'workspace-write','--ephemeral','--json','--cd',root,'-'],
  };
  if (route.provider === 'anthropic') return {
    command:'claude', args:['--print','--model',route.model,'--effort',route.effectiveEffort,'--output-format','json',...(pilot?['--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}']:[])],
  };
  fail('GUARDED_DEEPSEEK_PROFILE_REQUIRED');
}

// No shell, no fallback, no retries, and bounded captured output. Child output is
// parsed in memory; prompt bodies and CLI diagnostics never enter the ledger.
export function launchPrimary({command,args,prompt,root,timeoutMs=120000}) {
  return new Promise(resolve => {
    const started=Date.now();
    const child=spawn(command,args,{cwd:root,stdio:['pipe','pipe','pipe'],shell:false});
    let output='', exceeded=false, timedOut=false;
    const timer=setTimeout(()=>{timedOut=true;child.kill('SIGTERM');},timeoutMs);
    const killTimer=setTimeout(()=>child.kill('SIGKILL'),timeoutMs+5000);
    child.stdout.on('data',data=>{if(Buffer.byteLength(output)+data.length>1000000){exceeded=true;child.kill('SIGTERM');}else output+=data;});
    child.stderr.resume();
    child.on('error',()=>{clearTimeout(timer);clearTimeout(killTimer);resolve({status:'failed',output:'',exitCode:null,durationMs:Date.now()-started});});
    child.on('close',code=>{clearTimeout(timer);clearTimeout(killTimer);resolve({status:code===0&&!exceeded&&!timedOut?'succeeded':'failed',output,exitCode:code,durationMs:Date.now()-started});});
    child.stdin.on('error',()=>{});
    child.stdin.end(prompt);
  });
}

export function parsePrimaryOutput(output, provider) {
  const result={text:'',usage:{},execution:{}};
  const numbers=(usage,keys)=>Object.fromEntries(Object.entries(keys).filter(([,key])=>Number.isSafeInteger(usage?.[key])&&usage[key]>=0).map(([name,key])=>[name,usage[key]]));
  if(provider==='openai') {
    for(const line of output.split('\n')) {
      let event;try{event=JSON.parse(line);}catch{continue;}
      if(event.type==='turn.completed')result.usage=numbers(event.usage,{inputTokens:'input_tokens',outputTokens:'output_tokens',cachedInputTokens:'cached_input_tokens'});
      if(event.type==='item.completed'&&event.item?.type==='agent_message')result.text=event.item.text??'';
    }
  } else {
    try {
      const value=JSON.parse(output);
      result.text=typeof value.result==='string'?value.result:'';
      result.usage=numbers(value.usage,{inputTokens:'input_tokens',outputTokens:'output_tokens'});
      // A requested model or CLI alias is never evidence of actual identity.
      const models=Object.keys(value.modelUsage??{});
      if(models.length===1) result.execution={provider:'anthropic',actualModel:models[0],identitySource:'provider_response'};
    }catch{}
  }
  return result;
}

export async function routeTask({root=process.cwd(),task,quota={},ownerRequestedDeepSeek=false,ownerRequest,execute=false,pilot=false,capabilities,launch=launchPrimary,now=Date.now()}) {
  root=path.resolve(root);
  if(await realpath(root)!==root)fail('NONCANONICAL_PROJECT_ROOT');
  const adapter=await readInput(path.join(root,'config/model-project.json'));
  if(task.repository!==adapter.repository)fail('PROJECT_ADAPTER_MISMATCH');
  const remote=git(root,['remote','get-url','origin']).replace(/\.git$/,'');
  if(![`https://github.com/${task.repository}`,`git@github.com:${task.repository}`].includes(remote))fail('REPOSITORY_IDENTITY_MISMATCH');
  if(!/^[0-9a-f]{40}$/.test(task.headSha??'')||git(root,['rev-parse','HEAD'])!==task.headSha)fail('STALE_HEAD');
  if(!/^[a-z0-9][a-z0-9-]{0,63}$/.test(task.taskId??''))fail('INVALID_TASK_ID');
  if(pilot&&(task.taskType!=='routine'||task.risk!=='low'||task.complexity!=='simple'||task.overrides||task.history||ownerRequestedDeepSeek||ownerRequest))fail('PILOT_REQUIRES_ROUTINE_SYNTHETIC_TASK');
  if(task.baseSha!==undefined) {
    if(!/^[0-9a-f]{40}$/.test(task.baseSha))fail('INVALID_TASK_BASE');
    try {git(root,['merge-base','--is-ancestor',task.baseSha,task.headSha]);} catch {fail('INVALID_TASK_BASE');}
  }
  const route=resolveRoute({repository:task.repository,taskId:task.taskId,baseSha:task.baseSha,headSha:task.headSha,role:task.role,taskType:task.taskType,risk:task.risk,complexity:task.complexity,history:task.history,implementerFamily:task.implementerFamily,overrides:task.overrides,ownerRequestedDeepSeek,ownerRequest,quota,capabilities:capabilities??discoverCapabilities(),now});
  if(task.taskType==='release')fail('EXISTING_RELEASE_CAPTAIN_REQUIRED');
  const record=(execution={},usage={})=>decisionRecord({route,taskId:task.taskId,attempt:task.attempt??1,timestamp:now,execution,usage});
  // Validate telemetry identity before starting any child.
  record();
  if(!execute&&!pilot)return {route,record:record({status:'planned'}),status:'planned'};
  if(!pilot&&adapter.activation!=='approved')fail('ROUTING_ACTIVATION_APPROVAL_REQUIRED');
  if(route.provider==='deepseek')fail('GUARDED_DEEPSEEK_PROFILE_REQUIRED');
  if(route.availability!=='verified')fail('MODEL_AVAILABILITY_UNVERIFIED');
  const selectedQuota=route.quota?.[route.provider==='openai'?'codex':'claude'];
  if(['exhausted','rate_limited'].includes(selectedQuota?.state))fail('PRIMARY_CAPACITY_OWNER_DECISION_REQUIRED');
  const prompt=pilot?PILOT_PROMPT:task.instruction;
  if(typeof prompt!=='string'||!prompt.length||prompt.length>16000||containsRecognizedSecret(prompt)||containsSuspiciousHighEntropy(prompt))fail('UNSAFE_TASK_INSTRUCTION');
  if(git(root,['rev-parse','HEAD'])!==task.headSha)fail('STALE_HEAD');
  const command=primaryCommand(route,{root,pilot});
  const launched=await launch({...command,prompt,root});
  const parsed=parsePrimaryOutput(launched.output??'',route.provider);
  const status=launched.status==='succeeded'&&(!pilot||parsed.text.trim()==='# Router pilot')?'succeeded':'failed';
  return {route,record:record({...parsed.execution,status,durationMs:launched.durationMs,exitCode:launched.exitCode},parsed.usage),status,pilot,outputValidated:pilot?status==='succeeded':null};
}

export async function main(argv) {
  const options={};
  for(let i=0;i<argv.length;i++) {
    const key=argv[i];
    if(key==='--help'){console.log('agent-route --task FILE [--quota FILE] [--refresh-quota] [--output LEDGER] [--owner-request FILE] [--pilot | --execute]. Default: Codex/Claude selection only. DeepSeek requires a fresh task-scoped operator request file and the guarded profile. Pilot: fixed synthetic no-source task; production activation remains separate.');return;}
    if(['--execute','--pilot','--refresh-quota'].includes(key)){options[key.slice(2)]=true;continue;}
    if(!['--task','--quota','--output','--owner-request'].includes(key)||!argv[i+1]||argv[i+1].startsWith('--'))fail('INVALID_ARGUMENT');
    options[key.slice(2)]=argv[++i];
  }
  if(!options.task||options.pilot&&options.execute)fail('INVALID_MODE');
  const task=await readInput(path.resolve(options.task));
  const quota=options.quota?await readInput(path.resolve(options.quota)):{};
  if(options['refresh-quota'])quota.codex=await collectCodexQuota();
  const ownerRequest=options['owner-request']?await readInput(path.resolve(options['owner-request'])):undefined;
  const result=await routeTask({task,quota,ownerRequest,execute:options.execute,pilot:options.pilot});
  if(options.output)await appendDecisionRecord(path.resolve(options.output),result.record);
  console.log(JSON.stringify({...result.record,status:result.status,selectionAvailability:result.route.availability,
    primaryQuotaWarning:result.route.quotaWarning,reviewBlocked:result.route.reviewBlocked,
    limitation:result.route.availability!=='verified'?'MODEL_AVAILABILITY_UNVERIFIED':null,
    pilot:result.pilot??false,outputValidated:result.outputValidated??null}));
  if(result.status==='failed')process.exitCode=1;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main(process.argv.slice(2)).catch(error=>{console.error(`agent-route: ${/^[A-Z_]+$/.test(error.code??'')?error.code:'ROUTING_FAILED'}`);process.exitCode=1;});
