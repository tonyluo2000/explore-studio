import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {PassThrough,Writable} from 'node:stream';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {normalizeQuota,ownerQuotaReport,parseCodexRateLimits,collectCodexQuota} from '../scripts/model-quota.mjs';
import {discoverCapabilities,MODEL_CATALOG} from '../scripts/model-capabilities.mjs';
const now=Date.parse('2026-11-08T02:00:00Z');
const snapshot=(usedPercent,windowDurationMins=10080)=>({rateLimits:{primary:{usedPercent,windowDurationMins,resetsAt:now/1000+7200}}});

test('quota percentages come only from verified provider windows and threshold is configurable',()=>{
  const report=parseCodexRateLimits(snapshot(85),{now});assert.equal(report.state,'low');assert.equal(report.remainingPercent,15);assert.equal(report.window,'weekly');
  assert.equal(parseCodexRateLimits(snapshot(85),{now,lowThresholdPercent:10}).state,'healthy');
  assert.throws(()=>normalizeQuota(null,{lowThresholdPercent:101}),/INVALID_QUOTA_THRESHOLD/);
});
test('temporary rate limit is distinguished from weekly exhaustion',()=>{
  assert.equal(parseCodexRateLimits(snapshot(100),{now}).state,'exhausted');
  const temporary=parseCodexRateLimits(snapshot(100,5),{now});assert.equal(temporary.state,'rate_limited');assert.equal(temporary.window,'temporary');
  const both=snapshot(100,5);both.rateLimits.secondary=snapshot(100).rateLimits.primary;
  assert.equal(parseCodexRateLimits(both,{now}).state,'exhausted');
});
test('most constrained verified window wins and unrelated buckets do not replace codex',()=>{
  const data=snapshot(10,300);data.rateLimits.secondary=snapshot(95).rateLimits.primary;
  assert.equal(parseCodexRateLimits(data,{now}).remainingPercent,5);
  const multi={rateLimitsByLimitId:{codex:snapshot(90).rateLimits,other:snapshot(0).rateLimits},rateLimits:snapshot(0).rateLimits};
  assert.equal(parseCodexRateLimits(multi,{now}).state,'low');
});
test('explicit backend denial remains constrained regardless of percentages',()=>{
  assert.equal(parseCodexRateLimits({...snapshot(0),ordinaryUsageAllowed:false},{now}).state,'exhausted');
  assert.equal(parseCodexRateLimits({rateLimits:{spendControlReached:true}},{now}).state,'exhausted');
});
test('expired reset and missing visibility yield unknown without inferred recovery',()=>{
  const old=snapshot(100);old.rateLimits.primary.resetsAt=now/1000-1;
  assert.equal(parseCodexRateLimits(old,{now}).state,'unknown');
  assert.equal(parseCodexRateLimits({rateLimits:{}},{now}).state,'unknown');
  assert.equal(parseCodexRateLimits(null,{now}).remainingPercent,null);
});
test('explicit owner reports expire, do not manufacture numerical quota, and permit recovery',()=>{
  const low=ownerQuotaReport('low',{now});assert.equal(low.source,'owner');assert.equal(low.remainingPercent,null);
  assert.equal(normalizeQuota(low,{now:now+3_600_001}).state,'unknown');
  assert.equal(ownerQuotaReport('healthy',{now}).state,'healthy');
  assert.throws(()=>ownerQuotaReport('low',{now,ttlMs:86_400_001}),/INVALID_OWNER_QUOTA_REPORT/);
  assert.equal(normalizeQuota({...low,remainingPercent:2},{now}).remainingPercent,null);
});
test('unverified future malformed or indefinitely reusable reports become unknown',()=>{
  const report=ownerQuotaReport('low',{now});
  for(const data of [{state:'low'}, {...report,source:'guess'}, {...report,observedAt:new Date(now+1).toISOString()}, {...report,expiresAt:'tomorrow'}, {...report,expiresAt:new Date(now+2*86_400_000).toISOString()}]) assert.equal(normalizeQuota(data,{now}).state,'unknown');
});
test('metadata collector sends only initialize and single rate limit read, never a model turn',async()=>{
  const requests=[];
  const child=new EventEmitter();child.stdout=new PassThrough();child.kill=()=>{};
  child.stdin=new Writable({write(chunk,encoding,done){const request=JSON.parse(chunk);requests.push(request);queueMicrotask(()=>{
    if(request.id===1) child.stdout.write(JSON.stringify({id:1,result:{}})+'\n');
    if(request.id===2) child.stdout.write(JSON.stringify({id:2,result:snapshot(88)})+'\n');
  });done();}});
  const report=await collectCodexQuota({now,spawnProcess:(command,args,options)=>{assert.equal(command,'codex');assert.deepEqual(args,['app-server','--stdio']);assert.equal(options.shell,false);return child;}});
  assert.equal(report.state,'low');assert.deepEqual(requests.map(value=>value.method),['initialize','initialized','account/rateLimits/read']);
});
test('unavailable CLI or account metadata returns unknown without exposing diagnostics',async()=>{
  const report=await collectCodexQuota({now,spawnProcess:()=>{throw new Error('private account detail');}});
  assert.equal(report.state,'unknown');assert.ok(!JSON.stringify(report).includes('private'));
});
test('capability discovery narrows documented efforts and inspects no credential files',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'model-capability-'));
  try {
    const filename=path.join(root,'models.json');await writeFile(filename,JSON.stringify({fetched_at:new Date(now).toISOString(),models:[{slug:'gpt-6.1-sol',visibility:'list',supported_reasoning_levels:[{effort:'low'}]}]}));
    const commands=[];const capabilities=discoverCapabilities({now,codexCachePath:filename,exec:(command,args)=>{commands.push([command,args]);return command==='codex'?'codex-cli 0.164.0':'2.1.284 (Claude Code)';}});
    assert.deepEqual(commands,[['codex',['--version']],['claude',['--version']]]);
    const model=capabilities.models.find(value=>value.model==='gpt-6.1-sol');assert.equal(model.available,'verified');assert.deepEqual(model.efforts,['low']);
    assert.equal(capabilities.models.find(value=>value.model==='claude-sonnet-5-5').available,'unknown');
    assert.ok(!MODEL_CATALOG.some(value=>value.model==='deepseek-flash'));
  } finally {await rm(root,{recursive:true,force:true});}
});
test('missing or old agent CLIs do not advertise model availability',()=>{
  const capabilities=discoverCapabilities({now,codexCachePath:'/nonexistent',exec:command=>{if(command==='codex')throw Error('missing');return '2.1.100';}});
  assert.equal(capabilities.models.find(value=>value.model==='gpt-6-luna').available,false);
  assert.equal(capabilities.models.find(value=>value.model==='claude-sonnet-5-5').available,false);
});
