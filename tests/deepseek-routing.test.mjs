import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveRoute} from '../scripts/deepseek-routing.mjs';
const repository='tonyluo2000/mile-commons';
test('routine and feature routes select real provider IDs with explicit low effort',()=>{
  assert.equal(resolveRoute({repository,taskType:'routine'}).model,'deepseek-flash');
  const route=resolveRoute({repository,taskType:'implementation'});
  assert.equal(route.model,'deepseek-v4-pro');assert.equal(route.reasoningEffort,'low');assert.equal(route.automaticFallback,false);
});
test('review independence requires different model family, including Flash vs Pro',()=>{
  assert.throws(()=>resolveRoute({repository,taskType:'review',implementerFamily:'deepseek'}),/INDEPENDENT_MODEL_REQUIRED/);
  assert.throws(()=>resolveRoute({repository,taskType:'review'}),/IMPLEMENTER_FAMILY_REQUIRED/);
  assert.equal(resolveRoute({repository,taskType:'security',implementerFamily:'openai'}).family,'deepseek');
});
test('task overrides remain explicit and cannot impersonate provider or authorize release',()=>{
  assert.equal(resolveRoute({repository,taskType:'routine',overrides:{model:'deepseek-v4-pro'}}).model,'deepseek-v4-pro');
  assert.throws(()=>resolveRoute({repository,taskType:'routine',overrides:{family:'claude'}}),/INVALID_DEEPSEEK_ROUTE/);
  assert.equal(resolveRoute({repository,taskType:'release'}).model,null);
  assert.throws(()=>resolveRoute({repository:'unknown/project',taskType:'implementation'}),/UNAPPROVED_REPOSITORY/);
});
test('unknown providers cannot claim a trusted family',()=>{
 assert.throws(()=>resolveRoute({repository,taskType:'implementation',overrides:{provider:'untrusted',family:'deepseek'}}),/UNKNOWN_PROVIDER/);
});
