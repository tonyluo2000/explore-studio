import { readFileSync } from 'node:fs';
import { MODEL_CATALOG } from './model-capabilities.mjs';
import { normalizeQuota, CONSTRAINED_QUOTA_STATES } from './model-quota.mjs';
import { qualityRequirements, assertQualityFloor } from './model-quality.mjs';

const configuration = JSON.parse(readFileSync(new URL('../config/ai-model-routing.json', import.meta.url), 'utf8'));
const families = new Set(['deepseek', 'openai', 'claude']);
const efforts = ['low','medium','high'];
const constrained = quota => CONSTRAINED_QUOTA_STATES.includes(quota.state);
const fail = code => {throw Object.assign(new Error(code),{code});};
const primaryKey = provider => provider === 'openai' ? 'codex' : 'claude';
const sensitiveTypes = ['privacy','financial','tax','authorization','migration','release-tooling'];
const strongest = provider => provider === 'openai' ? 'gpt-6-astra' : 'claude-opus-5-5';
const normalModel = provider => provider === 'openai' ? 'gpt-6.1-sol' : 'claude-sonnet-5-5';
const maximumEffort = (...values) => efforts[Math.max(...values.map(value=>efforts.indexOf(value)))];
const complexities = new Set(['routine','simple','standard','complex','multi-file','architecture','difficult','difficult-debugging']);

export function resolveRoute({repository,taskType,role,implementerFamily,overrides={},risk,complexity,history={},quota={},capabilities,ownerRequestedDeepSeek,now=Date.now(),lowThresholdPercent=configuration.quota.lowThresholdPercent}={}) {
  if (ownerRequestedDeepSeek !== undefined && typeof ownerRequestedDeepSeek !== 'boolean') fail('INVALID_OWNER_DEEPSEEK_REQUEST');
  if (!Object.hasOwn(configuration.projects, repository)) fail('UNAPPROVED_REPOSITORY');
  if (taskType === 'release') return {authority:configuration.releaseAuthority,automatic:false,model:null,repository,taskType,approvalAuthority:'NONE'};
  const base = configuration.tasks[taskType] ?? (sensitiveTypes.includes(taskType) ? configuration.tasks.security : null);
  if (!base) fail('UNKNOWN_TASK_TYPE');
  if (complexity !== undefined && !complexities.has(complexity)) fail('INVALID_COMPLEXITY');
  if (role !== undefined && !['implementation','review'].includes(role)) fail('INVALID_TASK_ROLE');
  const reviewing = taskType === 'review' || role === 'review';
  if (reviewing && !families.has(implementerFamily)) fail('IMPLEMENTER_FAMILY_REQUIRED');
  if (!overrides || typeof overrides !== 'object' || Array.isArray(overrides) || Object.keys(overrides).some(key=>!['provider','model','family','reasoningEffort'].includes(key))) fail('INVALID_OVERRIDE');
  const quality = qualityRequirements({risk,complexity,taskType,history});
  const quotas = Object.fromEntries(['codex','claude'].map(key=>[key,normalizeQuota(quota[key],{...configuration.quota,lowThresholdPercent,now})]));
  const supplied = capabilities?.models ?? MODEL_CATALOG;
  if (!Array.isArray(supplied)) fail('INVALID_CAPABILITIES');
  // Capabilities may narrow the verified catalog; they cannot invent a provider,
  // trusted family, effort setting, or model merely by supplying those strings.
  const candidates = MODEL_CATALOG.map(entry=>{
    const found=supplied.find(value=>value.model===entry.model&&value.provider===entry.provider);
    return found ? {...entry,available:found.available,efforts:entry.efforts.filter(value=>found.efforts?.includes(value))} : {...entry,available:false,efforts:[]};
  });
  const candidate = model => candidates.find(entry=>entry.model===model);
  const suitable = (entry, effort) => entry && entry.available !== false && entry.efforts.includes(effort)
    && (quality.risk !== 'critical' || ['gpt-6-astra','claude-opus-5-5','deepseek-v4-pro'].includes(entry.model))
    && (!reviewing || entry.family !== implementerFamily);
  let effort=maximumEffort(base.reasoningEffort,quality.minimumEffort);
  let provider=reviewing ? (implementerFamily === 'claude' ? 'openai' : 'anthropic') : base.primary==='claude' ? 'anthropic' : 'openai';
  const rolePrimary=primaryKey(provider);
  let model=effort==='high' ? strongest(provider) : reviewing ? normalModel(provider) : base.model;
  let reason=null;
  const overrideModel=overrides.model ? candidate(overrides.model) : null;
  if(overrides.model && !overrideModel) fail('UNSUPPORTED_MODEL');
  if(overrides.provider && !['openai','anthropic','deepseek'].includes(overrides.provider)) fail('UNKNOWN_PROVIDER');
  if(overrides.family && !families.has(overrides.family)) fail('INVALID_ROUTE');
  if(overrides.reasoningEffort && !efforts.includes(overrides.reasoningEffort)) fail('UNSUPPORTED_REASONING_EFFORT');
  if(overrideModel && ((overrides.provider && overrides.provider!==overrideModel.provider)||(overrides.family&&overrides.family!==overrideModel.family))) fail('PROVIDER_FAMILY_MISMATCH');
  if(overrides.reasoningEffort) {
    effort=overrides.reasoningEffort;
    assertQualityFloor({requestedEffort:effort,requirements:quality});
  }
  const requestedEffort=effort;
  // Only an explicit operator-side owner request can opt into DeepSeek.
  // A quota warning, provider/model field, or source manifest is not authority.
  const wantsDeepSeek=overrideModel?.provider==='deepseek'||overrides.provider==='deepseek'||overrides.family==='deepseek';
  if(wantsDeepSeek && ownerRequestedDeepSeek !== true) fail('DEEPSEEK_OWNER_REQUEST_REQUIRED');
  if(ownerRequestedDeepSeek === true && (overrideModel && overrideModel.provider!=='deepseek' || overrides.provider && overrides.provider!=='deepseek' || overrides.family && overrides.family!=='deepseek')) fail('OWNER_REQUEST_MODEL_CONFLICT');
  if(ownerRequestedDeepSeek !== true && (overrideModel || overrides.provider)) {
    provider=overrideModel?.provider ?? overrides.provider;
    model=overrideModel?.model ?? (effort==='high' ? strongest(provider) : normalModel(provider));
  }
  let selected=candidate(model);
  const targetPrimary=ownerRequestedDeepSeek === true ? rolePrimary : primaryKey(provider);
  if(ownerRequestedDeepSeek === true) {
    const backup=candidate(configuration.backup.model);
    const backupEffort=effort==='low' ? 'low' : 'high';
    if(overrides.reasoningEffort==='medium') fail('UNSUPPORTED_REASONING_EFFORT');
    if(!suitable(backup,backupEffort)) fail(reviewing&&backup?.family===implementerFamily ? 'INDEPENDENT_MODEL_REQUIRED' : 'NO_SUITABLE_BACKUP');
    selected=backup;effort=backupEffort;reason='OWNER_EXPLICIT_REQUEST';
  }
  if(!reason) {
    if(overrides.family && overrides.family!==selected?.family) fail('PROVIDER_FAMILY_MISMATCH');
    // Missing/unsupported primary capabilities never activate a paid provider.
    // Try another suitable primary family, retaining the quality floor.
    if(!suitable(selected,effort) || ['exhausted','rate_limited'].includes(quotas[primaryKey(selected?.provider)].state)) {
      const alternateProvider=provider==='openai' ? 'anthropic' : 'openai';
      const alternate=candidate(effort==='high' ? strongest(alternateProvider) : normalModel(alternateProvider));
      if(overrideModel || overrides.provider || !suitable(alternate,effort) || ['exhausted','rate_limited'].includes(quotas[primaryKey(alternateProvider)].state)) fail(reviewing ? 'INDEPENDENT_MODEL_REQUIRED' : 'NO_SUITABLE_MODEL');
      selected=alternate;
    }
  }
  if(!suitable(selected,effort)) fail(reviewing ? 'INDEPENDENT_MODEL_REQUIRED' : 'NO_SUITABLE_MODEL');
  if(selected.provider==='deepseek' && (ownerRequestedDeepSeek !== true || !reason || effort==='medium')) fail('DEEPSEEK_OWNER_REQUEST_REQUIRED');
  assertQualityFloor({requestedEffort:effort,requirements:quality});
  const gates=[...quality.gates,'REVIEWED_ACTIVATION_REQUIRED'];
  if(selected.provider==='deepseek') gates.push('EXTERNAL_TRANSFER_AUTHORIZATION_REQUIRED','PAID_CALL_AUTHORIZATION_REQUIRED','SPENDING_LIMIT_REQUIRED','INDEPENDENT_SECURITY_REVIEW_REQUIRED');
  let reviewer=null;
  if(!reviewing) {
    const reviewerProvider=selected.family==='claude' ? 'openai' : 'anthropic';
    const reviewerEffort=quality.independentReviewRequired ? 'high' : 'medium';
    const reviewerModel=candidate(reviewerEffort==='high' ? strongest(reviewerProvider) : normalModel(reviewerProvider));
    const reviewerQuota=quotas[primaryKey(reviewerProvider)];
    if(suitable(reviewerModel,reviewerEffort) && !['exhausted','rate_limited'].includes(reviewerQuota.state)) reviewer={provider:reviewerModel.provider,model:reviewerModel.model,family:reviewerModel.family,reasoningEffort:reviewerEffort};
    else if(selected.family==='deepseek') {
      const alternateProvider=reviewerProvider==='openai' ? 'anthropic' : 'openai';
      const alternate=candidate(reviewerEffort==='high' ? strongest(alternateProvider) : normalModel(alternateProvider));
      if(suitable(alternate,reviewerEffort) && !['exhausted','rate_limited'].includes(quotas[primaryKey(alternateProvider)].state)) reviewer={provider:alternate.provider,model:alternate.model,family:alternate.family,reasoningEffort:reviewerEffort};
    }
  }
  return {provider:selected.provider,model:selected.model,family:selected.family,reasoningEffort:effort,requestedEffort,effectiveEffort:effort,
    availability:selected.available ?? 'unknown',repository,taskType,role:reviewing?'review':'implementation',risk:quality.risk,complexity:complexity??'unknown',
    quota:quotas,primaryQuota:quotas,primaryRole:targetPrimary,backupReason:reason,ownerRequestedDeepSeek:ownerRequestedDeepSeek===true,quotaWarning:constrained(quotas[targetPrimary]) ? `PRIMARY_${quotas[targetPrimary].state.toUpperCase()}` : null,reviewer,independentReviewRequired:quality.independentReviewRequired,
    reviewBlocked:!reviewing&&quality.independentReviewRequired&&!reviewer,gates,reasons:quality.reasons,
    automaticFallback:false,automatic:false,selection:'before-task',approvalAuthority:'NONE'};
}
