import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { homedir } from 'node:os';
import path from 'node:path';

// Supported settings are separate from account access. These documented
// capabilities do not assert that a subscription can currently run the model.
// https://developers.openai.com/api/docs/guides/reasoning
// https://code.claude.com/docs/en/model-config
// https://api-docs.deepseek.com/quick_start/pricing/
export const MODEL_CATALOG = Object.freeze([
  {provider:'openai',model:'gpt-6-luna',family:'openai',efforts:['low','medium','high'],available:'unknown',source:'official-docs'},
  {provider:'openai',model:'gpt-6.1-sol',family:'openai',efforts:['low','medium','high'],available:'unknown',source:'official-docs'},
  {provider:'openai',model:'gpt-6-astra',family:'openai',efforts:['low','medium','high'],available:'unknown',source:'official-docs'},
  {provider:'anthropic',model:'claude-sonnet-5-5',family:'claude',efforts:['low','medium','high'],available:'unknown',source:'official-docs'},
  {provider:'anthropic',model:'claude-opus-5-5',family:'claude',efforts:['low','medium','high'],available:'unknown',source:'official-docs'},
  {provider:'deepseek',model:'deepseek-v4-pro',family:'deepseek',efforts:['low','high'],available:'unknown',source:'official-docs'},
  {provider:'deepseek',model:'deepseek-flash',family:'deepseek',efforts:['low'],available:'unknown',source:'official-docs'}
]);

function versionAtLeast(version, minimum) {
  if (!version) return false;
  const actual=version.split('.').map(Number), floor=minimum.split('.').map(Number);
  for (let index=0;index<3;index++) {if(actual[index]!==floor[index]) return actual[index]>floor[index];}
  return true;
}

export function discoverCapabilities({codexCachePath=path.join(homedir(),'.codex','models_cache.json'),exec=execFileSync,now=Date.now(),cacheMaxAgeMs=86_400_000}={}) {
  const version = command => {
    try {return exec(command,['--version'],{encoding:'utf8',timeout:3000,stdio:['ignore','pipe','ignore']}).match(/\d+\.\d+\.\d+/)?.[0] ?? null;} catch {return null;}
  };
  const codexCli=version('codex'),claudeCli=version('claude');
  let cache=null;
  try {const data=JSON.parse(readFileSync(codexCachePath,'utf8'));if(Date.parse(data.fetched_at)<=now && now-Date.parse(data.fetched_at)<=cacheMaxAgeMs && Array.isArray(data.models)) cache=data; } catch { /* No credentials or session logs are inspected. */ }
  const models=MODEL_CATALOG.map(entry=>{
    if(entry.provider === 'openai') {
      const match=cache?.models.find(model=>model.slug === entry.model && model.visibility === 'list');
      return {...entry,efforts:match ? entry.efforts.filter(effort=>match.supported_reasoning_levels?.some(value=>value.effort===effort)) : entry.efforts,available:!codexCli ? false : match ? 'verified' : 'unknown',source:match ? 'codex-model-cache' : entry.source};
    }
    if(entry.provider === 'anthropic') return {...entry,available:versionAtLeast(claudeCli,entry.model==='claude-sonnet-5-5' ? '2.1.284' : '2.1.280') ? 'unknown' : false};
    return {...entry};
  });
  return {models,codexCli,claudeCli};
}
