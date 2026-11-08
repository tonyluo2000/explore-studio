import test from 'node:test';
import assert from 'node:assert/strict';
import {assertOwnerTaskRequest,assertCallAuthorization,OWNER_REQUEST_SCHEMA,CALL_AUTHORIZATION_SCHEMA} from '../scripts/model-authorization.mjs';
const now=Date.UTC(2026,10,7,22);
const scope={repository:'tonyluo2000/mile-commons',taskId:'scope-test',role:'implementation',baseSha:'a'.repeat(40),headSha:'b'.repeat(40)};
const owner=()=>({schema:OWNER_REQUEST_SCHEMA,authorizationId:'owner-test-0001',...scope,model:'deepseek-v4-pro',issuedAt:new Date(now-1000).toISOString(),expiresAt:new Date(now+3600000).toISOString(),authorizationReference:'owner:test'});
const call=()=>({...owner(),schema:CALL_AUTHORIZATION_SCHEMA,requestId:'c'.repeat(64),bodySha256:'d'.repeat(64),reasoningEffort:'low',maxCostUsd:0.1,transferApproved:true,paymentApproved:true});
const validate=authorization=>assertCallAuthorization({authorization,ownerRequest:owner(),scope,requestId:'c'.repeat(64),bodySha256:'d'.repeat(64),reasoningEffort:'low',maxCostUsd:0.1,now});
test('selection requires a fresh exact-task owner record, never a boolean',()=>{
 assert.equal(assertOwnerTaskRequest({request:owner(),scope,now}).authorizationId,'owner-test-0001');
 for(const request of [undefined,null]) assert.throws(()=>assertOwnerTaskRequest({request,scope,now}),{code:'OWNER_TASK_REQUEST_REQUIRED'});
 for(const request of [true,{ownerRequestedDeepSeek:true},{...owner(),schema:'old'},{...owner(),authorizationId:'x'}]) assert.throws(()=>assertOwnerTaskRequest({request,scope,now}),{code:'INVALID_OWNER_TASK_REQUEST'});
});
test('prior task, project, role, base and HEAD grants cannot authorize this task',()=>{
 for(const [key,value] of [['repository','briersystems/montefinance'],['taskId','other-task'],['role','review'],['baseSha','e'.repeat(40)],['headSha','f'.repeat(40)]]) assert.throws(()=>assertOwnerTaskRequest({request:{...owner(),[key]:value},scope,now}),{code:'OWNER_TASK_SCOPE_MISMATCH'});
});
test('expired, future, unbounded and malformed owner grants fail closed',()=>{
 for(const request of [{...owner(),expiresAt:new Date(now).toISOString()},{...owner(),issuedAt:new Date(now+1000).toISOString()},{...owner(),expiresAt:new Date(now+86400001).toISOString()},{...owner(),issuedAt:'invalid'}]) assert.throws(()=>assertOwnerTaskRequest({request,scope,now}),{code:'OWNER_TASK_REQUEST_EXPIRED'});
});
test('model selection alone grants no transfer or paid permission',()=>{
 assert.throws(()=>validate(undefined),{code:'CALL_AUTHORIZATION_REQUIRED'});
 assert.throws(()=>validate({...call(),transferApproved:false}),{code:'SOURCE_TRANSFER_AUTHORIZATION_REQUIRED'});
 assert.throws(()=>validate({...call(),paymentApproved:false}),{code:'PAID_CALL_AUTHORIZATION_REQUIRED'});
 assert.equal(validate(call()).bodySha256,'d'.repeat(64));
});
test('each call binds owner identity, exact body, request, model, effort and spending cap',()=>{
 for(const [patch,code] of [[{authorizationId:'another-owner-01'},'CALL_AUTHORIZATION_ID_MISMATCH'],[{taskId:'different-task'},'CALL_AUTHORIZATION_SCOPE_MISMATCH'],[{bodySha256:'e'.repeat(64)},'CALL_AUTHORIZATION_BODY_MISMATCH'],[{requestId:'f'.repeat(64)},'CALL_AUTHORIZATION_REQUEST_MISMATCH'],[{reasoningEffort:'high'},'CALL_AUTHORIZATION_EFFORT_MISMATCH'],[{maxCostUsd:1},'CALL_AUTHORIZATION_SPENDING_MISMATCH'],[{model:'deepseek-flash'},'CALL_AUTHORIZATION_MODEL_MISMATCH'],[{expiresAt:new Date(now+7200000).toISOString()},'CALL_AUTHORIZATION_EXPIRED']]) assert.throws(()=>validate({...call(),...patch}),{code});
});
