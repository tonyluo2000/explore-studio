// Operator-supplied owner intent and exact-call permission are distinct records.
// These local records do not authenticate a person: the trusted operator must
// provide them separately from repository source, manifests, and model output.
export const OWNER_REQUEST_SCHEMA = 'cross-project.deepseek-owner-request.v1';
export const CALL_AUTHORIZATION_SCHEMA = 'cross-project.deepseek-call-authorization.v1';
const REPOSITORIES = new Set(['tonyluo2000/mile-commons','briersystems/montefinance','tonyluo2000/explore-studio']);
const SHA = /^[a-f0-9]{40}$/;
const HASH = /^[a-f0-9]{64}$/;
const ID = /^[a-z0-9][a-z0-9-]{7,95}$/;
const TASK = /^[a-z0-9][a-z0-9-]{0,63}$/;
const SCOPE_KEYS = ['repository','taskId','role','baseSha','headSha'];
const fail = code => {throw Object.assign(new Error(code),{code});};
const timestamp = value => typeof value === 'number' ? value : value instanceof Date ? value.getTime() : Date.parse(value);
const plain = value => value && typeof value === 'object' && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
function exactKeys(value, allowed, code) {
  if(!plain(value) || Object.keys(value).some(key=>!allowed.includes(key))) fail(code);
}
function validateScope(scope) {
  if(!plain(scope) || !REPOSITORIES.has(scope.repository) || !TASK.test(scope.taskId??'') || !['implementation','review'].includes(scope.role) || !SHA.test(scope.baseSha??'') || !SHA.test(scope.headSha??'')) fail('INVALID_TASK_AUTHORIZATION_SCOPE');
  return Object.fromEntries(SCOPE_KEYS.map(key=>[key,scope[key]]));
}
function bindScope(record, scope, code) {
  const safeScope=validateScope(scope);
  if(SCOPE_KEYS.some(key=>record[key]!==safeScope[key])) fail(code);
  return safeScope;
}
function validity(record, now, code) {
  const observed=timestamp(now),issued=timestamp(record.issuedAt),expires=timestamp(record.expiresAt);
  if(!Number.isFinite(observed) || typeof record.issuedAt!=='string' || typeof record.expiresAt!=='string' || !Number.isFinite(issued) || !Number.isFinite(expires) || issued>observed || expires<=observed || expires<=issued || expires-issued>86_400_000) fail(code);
  return {issuedAt:new Date(issued).toISOString(),expiresAt:new Date(expires).toISOString()};
}
function identity(record, code) {
  if(!ID.test(record.authorizationId??'') || record.model!=='deepseek-v4-pro' || typeof record.authorizationReference!=='string' || !/^[a-zA-Z0-9:/#._?-]{1,300}$/.test(record.authorizationReference)) fail(code);
}
export function assertOwnerTaskRequest({request,scope,now=Date.now()}={}) {
  if(!request) fail('OWNER_TASK_REQUEST_REQUIRED');
  exactKeys(request,['schema','authorizationId',...SCOPE_KEYS,'model','issuedAt','expiresAt','authorizationReference'],'INVALID_OWNER_TASK_REQUEST');
  if(request.schema!==OWNER_REQUEST_SCHEMA) fail('INVALID_OWNER_TASK_REQUEST');
  identity(request,'INVALID_OWNER_TASK_REQUEST');
  const safeScope=bindScope(request,scope,'OWNER_TASK_SCOPE_MISMATCH');
  const valid=validity(request,now,'OWNER_TASK_REQUEST_EXPIRED');
  return {schema:OWNER_REQUEST_SCHEMA,authorizationId:request.authorizationId,...safeScope,model:request.model,...valid,authorizationReference:request.authorizationReference};
}
export function assertCallAuthorization({authorization,ownerRequest,scope,requestId,bodySha256,reasoningEffort,maxCostUsd,now=Date.now()}={}) {
  const owner=assertOwnerTaskRequest({request:ownerRequest,scope,now});
  if(!authorization) fail('CALL_AUTHORIZATION_REQUIRED');
  exactKeys(authorization,['schema','authorizationId',...SCOPE_KEYS,'model','requestId','bodySha256','reasoningEffort','maxCostUsd','transferApproved','paymentApproved','issuedAt','expiresAt','authorizationReference'],'INVALID_CALL_AUTHORIZATION');
  if(authorization.schema!==CALL_AUTHORIZATION_SCHEMA) fail('INVALID_CALL_AUTHORIZATION');
  identity(authorization,'INVALID_CALL_AUTHORIZATION');
  if(authorization.authorizationId!==owner.authorizationId) fail('CALL_AUTHORIZATION_ID_MISMATCH');
  const safeScope=bindScope(authorization,scope,'CALL_AUTHORIZATION_SCOPE_MISMATCH');
  const valid=validity(authorization,now,'CALL_AUTHORIZATION_EXPIRED');
  if(timestamp(valid.issuedAt)<timestamp(owner.issuedAt) || timestamp(valid.expiresAt)>timestamp(owner.expiresAt)) fail('CALL_AUTHORIZATION_EXPIRED');
  if(!HASH.test(requestId??'') || authorization.requestId!==requestId) fail('CALL_AUTHORIZATION_REQUEST_MISMATCH');
  if(!HASH.test(bodySha256??'') || authorization.bodySha256!==bodySha256) fail('CALL_AUTHORIZATION_BODY_MISMATCH');
  if(!['low','high'].includes(reasoningEffort) || authorization.reasoningEffort!==reasoningEffort) fail('CALL_AUTHORIZATION_EFFORT_MISMATCH');
  if(!Number.isFinite(maxCostUsd) || maxCostUsd<=0 || maxCostUsd>1 || authorization.maxCostUsd!==maxCostUsd) fail('CALL_AUTHORIZATION_SPENDING_MISMATCH');
  if(authorization.transferApproved!==true) fail('SOURCE_TRANSFER_AUTHORIZATION_REQUIRED');
  if(authorization.paymentApproved!==true) fail('PAID_CALL_AUTHORIZATION_REQUIRED');
  return {schema:CALL_AUTHORIZATION_SCHEMA,authorizationId:owner.authorizationId,...safeScope,model:owner.model,requestId,bodySha256,reasoningEffort,maxCostUsd,transferApproved:true,paymentApproved:true,...valid,authorizationReference:authorization.authorizationReference};
}
