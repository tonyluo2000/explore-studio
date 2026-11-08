import test from 'node:test';
import assert from 'node:assert/strict';
import {sourcePolicyDigest,assertSourceActivation,assertPrimaryRoutingActivation} from '../scripts/model-activation.mjs';
const repository='tonyluo2000/mile-commons';
function fixture(schema='cross-project.deepseek-activation.v1') {
 const digest=sourcePolicyDigest();
 return {schema,repository,activationId:'owner-activation-001',ownerApproved:true,ownerApprovalReference:'synthetic:activation-test-only',sourcePolicyDigest:digest,roles:['implementation','review'],independentReview:{provider:'anthropic',actualModel:'claude-sonnet-5-5',outcome:'clean',substantiveDefects:0,participatedInImplementation:false,sourcePolicyDigest:digest,baseSha:'a'.repeat(40),headSha:'b'.repeat(40),receiptSha256:'c'.repeat(64),sourceBundleSha256:'d'.repeat(64)}};
}
test('default remains inactive; source policy has a deterministic content digest',()=>{
 assert.match(sourcePolicyDigest(),/^[a-f0-9]{64}$/);assert.equal(sourcePolicyDigest(),sourcePolicyDigest());
 assert.throws(()=>assertSourceActivation({repository}),{code:'POLICY_REVIEW_REQUIRED'});
});
test('reviewed operator activation binds repository and exact policy bytes without source edits',()=>{
 const activation=fixture();assert.equal(assertSourceActivation({repository,activation}).activationId,activation.activationId);
 for(const patch of [{repository:'briersystems/montefinance'},{ownerApproved:false},{sourcePolicyDigest:'0'.repeat(64)},{roles:['review']}]) assert.throws(()=>assertSourceActivation({repository,activation:{...activation,...patch}}),{code:'SOURCE_ACTIVATION_INVALID'});
});
test('DeepSeek or stale, unclean, same-author review cannot qualify its transfer controls',()=>{
 const activation=fixture();
 for(const patch of [{provider:'deepseek',actualModel:'deepseek-v4-pro'},{sourcePolicyDigest:'0'.repeat(64)},{substantiveDefects:1},{outcome:'incomplete'},{participatedInImplementation:true},{actualModel:'sonnet'},{receiptSha256:'missing'}]) assert.throws(()=>assertSourceActivation({repository,activation:{...activation,independentReview:{...activation.independentReview,...patch}}}),{code:'INDEPENDENT_POLICY_REVIEW_REQUIRED'});
});
test('primary and DeepSeek activations are distinct and grant no task or spending authorization',()=>{
 const primary=fixture('cross-project.primary-routing-activation.v1');assert.ok(assertPrimaryRoutingActivation({repository,activation:primary}));
 assert.throws(()=>assertSourceActivation({repository,activation:primary}),{code:'SOURCE_ACTIVATION_INVALID'});
 assert.throws(()=>assertPrimaryRoutingActivation({repository,activation:fixture()}),{code:'SOURCE_ACTIVATION_INVALID'});
 assert.equal(Object.hasOwn(primary,'paymentApproved'),false);assert.equal(Object.hasOwn(primary,'taskId'),false);
});


test('reviewed control identity comes only from the validated review record', () => {
  const activation = fixture();
  activation.reviewedControlSha = 'e'.repeat(40);
  const validated = assertSourceActivation({repository,activation});
  assert.equal(validated.reviewedControlSha,activation.independentReview.headSha);
  assert.notEqual(validated.reviewedControlSha,activation.reviewedControlSha);
});
