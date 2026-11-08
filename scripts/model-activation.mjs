import {createHash} from 'node:crypto';
import {readFileSync,lstatSync} from 'node:fs';

// A reusable capability activation is distinct from consent for a task or call.
// The trusted operator supplies it only after independent review and owner
// approval. It authenticates no person and never grants payment/source consent.
const POLICY_FILES = Object.freeze([
  'config/ai-model-routing.json',
  'scripts/model-activation.mjs','scripts/model-authorization.mjs',
  'scripts/model-quality.mjs','scripts/model-capabilities.mjs','scripts/model-quota.mjs',
  'scripts/deepseek-routing.mjs','scripts/deepseek-transfer-policy.mjs',
  'scripts/deepseek-source-classification.mjs','scripts/deepseek-source-scanner.mjs',
  'scripts/deepseek-budget.mjs','scripts/deepseek-agent.mjs',
  'scripts/deepseek-review-core.mjs','scripts/deepseek-review.mjs',
  'scripts/deepseek.mjs','scripts/deepseek-hosted-budget.mjs','scripts/deepseek-hosted-review.mjs',
  'scripts/agent-route.mjs','scripts/model-telemetry.mjs','scripts/deepseek-review-cache-policy.mjs',
]);
const PROJECTS = new Set(['tonyluo2000/mile-commons','briersystems/montefinance','tonyluo2000/explore-studio']);
const fail = code => {throw Object.assign(new Error(code),{code});};
const SHA=/^[a-f0-9]{40}$/,HASH=/^[a-f0-9]{64}$/;
const reference=value=>typeof value==='string' && /^[A-Za-z0-9:/#._?-]{1,300}$/.test(value);
export function sourcePolicyDigest() {
  const hash=createHash('sha256');
  for(const filename of POLICY_FILES) {
    const url=new URL('../'+filename,import.meta.url),stat=lstatSync(url);
    if(!stat.isFile() || stat.isSymbolicLink() || stat.size>256000) fail('POLICY_SOURCE_IDENTITY_INVALID');
    hash.update(filename+'\0').update(readFileSync(url)).update('\0');
  }
  return hash.digest('hex');
}
function validateActivation({activation,repository},schema) {
  if(!activation) fail('POLICY_REVIEW_REQUIRED');
  const review=activation.independentReview;
  const expected=sourcePolicyDigest();
  if(activation.schema!==schema
    || !PROJECTS.has(repository) || activation.repository!==repository
    || activation.ownerApproved!==true || !reference(activation.ownerApprovalReference)
    || !/^[a-z0-9][a-z0-9-]{7,95}$/.test(activation.activationId??'')
    || activation.sourcePolicyDigest!==expected
    || !Array.isArray(activation.roles) || activation.roles.length!==2
    || !['implementation','review'].every(role=>activation.roles.includes(role))) fail('SOURCE_ACTIVATION_INVALID');
  // DeepSeek cannot qualify changes to its own source-transfer protections.
  if(review?.provider!=='anthropic' || !['claude-sonnet-5-5','claude-opus-5-5'].includes(review.actualModel)
    || review.outcome!=='clean' || review.substantiveDefects!==0 || review.participatedInImplementation!==false
    || review.sourcePolicyDigest!==expected || !SHA.test(review.baseSha??'') || !SHA.test(review.headSha??'')
    || !HASH.test(review.receiptSha256??'') || !HASH.test(review.sourceBundleSha256??'')) fail('INDEPENDENT_POLICY_REVIEW_REQUIRED');
  return {activationId:activation.activationId,sourcePolicyDigest:expected,repository,reviewedControlSha:review.headSha};
}

export function assertSourceActivation(options={}) { return validateActivation(options,'cross-project.deepseek-activation.v1'); }
export function assertPrimaryRoutingActivation(options={}) { return validateActivation(options,'cross-project.primary-routing-activation.v1'); }
