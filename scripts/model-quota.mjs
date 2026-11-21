import { spawn } from 'node:child_process';

export const CONSTRAINED_QUOTA_STATES = Object.freeze(['low','exhausted','rate_limited','imminent']);
const STATES = new Set(['unknown','healthy',...CONSTRAINED_QUOTA_STATES]);
const iso = value => new Date(value).toISOString();
const unknown = () => ({state:'unknown',source:'unavailable',observedAt:null,expiresAt:null,remainingPercent:null,window:'unknown'});
const time = value => typeof value === 'number' ? value : Date.parse(value);

// Only provider observations and explicit owner reports count as quota evidence.
// Expired evidence becomes unknown; a passed reset time is never proof of recovery.
export function normalizeQuota(report, {now=Date.now(),lowThresholdPercent=20,maxAgeMs=900_000,ownerMaxAgeMs=86_400_000}={}) {
  if (!Number.isFinite(lowThresholdPercent) || lowThresholdPercent <= 0 || lowThresholdPercent >= 100) throw new Error('INVALID_QUOTA_THRESHOLD');
  if (!report || typeof report !== 'object' || !['owner','provider'].includes(report.source) || !STATES.has(report.state)) return unknown();
  const observed = time(report.observedAt), expires = time(report.expiresAt);
  const maximumAge = report.source === 'owner' ? ownerMaxAgeMs : maxAgeMs;
  if (!Number.isFinite(observed) || !Number.isFinite(expires) || observed > now || expires <= now || expires <= observed || now-observed > maximumAge || expires-observed > maximumAge) return unknown();
  const remaining = report.source === 'provider' && Number.isFinite(report.remainingPercent) && report.remainingPercent >= 0 && report.remainingPercent <= 100 ? report.remainingPercent : null;
  let state = report.state;
  if (remaining !== null && !['exhausted','rate_limited','imminent'].includes(state)) state = remaining === 0 ? (report.window === 'weekly' ? 'exhausted' : 'rate_limited') : remaining <= lowThresholdPercent ? 'low' : 'healthy';
  return {state,source:report.source,observedAt:iso(observed),expiresAt:iso(expires),remainingPercent:remaining,window:['weekly','temporary'].includes(report.window) ? report.window : 'unknown'};
}

export function ownerQuotaReport(state, {now=Date.now(),ttlMs=3_600_000,window='unknown'}={}) {
  if (!STATES.has(state) || !Number.isFinite(ttlMs) || ttlMs <= 0 || ttlMs > 86_400_000) throw new Error('INVALID_OWNER_QUOTA_REPORT');
  return normalizeQuota({state,source:'owner',observedAt:iso(now),expiresAt:iso(now+ttlMs),window},{now});
}

// Installed codex-cli 0.164.0 protocol: account/rateLimits/read.
// Source: https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt
export function parseCodexRateLimits(response, {now=Date.now(),lowThresholdPercent=20,maxAgeMs=900_000}={}) {
  const snapshot = response?.rateLimitsByLimitId?.codex ?? response?.rateLimits;
  if (!snapshot || typeof snapshot !== 'object') return unknown();
  const windows = [snapshot.primary,snapshot.secondary].filter(value => value && Number.isFinite(value.usedPercent) && value.usedPercent >= 0 && value.usedPercent <= 100 && (value.resetsAt == null || value.resetsAt*1000 > now));
  const limiting = windows.sort((a,b)=>b.usedPercent-a.usedPercent || (b.windowDurationMins??0)-(a.windowDurationMins??0))[0];
  const denied = response.ordinaryUsageAllowed === false || snapshot.spendControlReached === true || snapshot.rateLimitReachedType != null;
  if (!limiting && !denied && response.ordinaryUsageAllowed !== true) return unknown();
  const window = limiting ? (limiting.windowDurationMins >= 10_080 ? 'weekly' : Number.isFinite(limiting.windowDurationMins) ? 'temporary' : 'unknown') : 'unknown';
  const remainingPercent = limiting ? 100-limiting.usedPercent : null;
  const state = denied ? (window === 'temporary' && snapshot.rateLimitReachedType === 'rate_limit_reached' ? 'rate_limited' : 'exhausted') : remainingPercent === 0 ? (window === 'weekly' ? 'exhausted' : 'rate_limited') : remainingPercent !== null && remainingPercent <= lowThresholdPercent ? 'low' : 'healthy';
  const expires = Math.min(now+maxAgeMs,...windows.map(value=>value.resetsAt == null ? Infinity : value.resetsAt*1000));
  return normalizeQuota({state,source:'provider',observedAt:iso(now),expiresAt:iso(expires),remainingPercent,window},{now,lowThresholdPercent,maxAgeMs});
}

// One bounded metadata request. No thread/turn creation, token-generating probe,
// credential file reads, reset-credit consumption, retries, or polling loop.
export function collectCodexQuota({timeoutMs=5000,now=Date.now(),lowThresholdPercent=20,spawnProcess=spawn}={}) {
  return new Promise(resolve=>{
    let child, buffer='', totalBytes=0, finished=false;
    const finish = value => {
      if (finished) return;
      finished=true; clearTimeout(timer);
      child?.stdin?.end(); child?.kill();
      resolve(value);
    };
    const timer = setTimeout(()=>finish(unknown()),Math.min(Math.max(timeoutMs,100),10_000));
    try {child=spawnProcess('codex',['app-server','--stdio'],{stdio:['pipe','pipe','ignore'],shell:false});}
    catch {finish(unknown());return;}
    child.on('error',()=>finish(unknown()));
    child.on('exit',()=>finish(unknown()));
    child.stdin.on('error',()=>finish(unknown()));
    const send = value => child.stdin.write(JSON.stringify(value)+'\n');
    child.stdout.on('data',data=>{
      totalBytes+=data.length;
      if (totalBytes > 1_000_000) {finish(unknown());return;}
      buffer+=data.toString();
      let end;
      while ((end=buffer.indexOf('\n')) !== -1) {
        const line=buffer.slice(0,end); buffer=buffer.slice(end+1);
        let message;
        try {message=JSON.parse(line);} catch {continue;}
        if (message.id === 1) {
          if (!message.result || message.error) {finish(unknown());return;}
          send({method:'initialized'});
          send({id:2,method:'account/rateLimits/read'});
        }
        if (message.id === 2) {finish(message.error ? unknown() : parseCodexRateLimits(message.result,{now,lowThresholdPercent}));return;}
      }
    });
    send({id:1,method:'initialize',params:{clientInfo:{name:'cross-project-router',version:'1.0.0'},capabilities:{experimentalApi:true}}});
  });
}
