import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,mkdir,readFile,rm,symlink,realpath} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {prepareImplementation,runImplementation,validateImplementationResponse,applyImplementation,createIsolatedWorktree} from '../scripts/deepseek-agent.mjs';
async function fixture(t){
 const root=await realpath(await mkdtemp(path.join(tmpdir(),'deepseek-agent-'))); t.after(()=>rm(root,{recursive:true,force:true}));
 const git=(...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
 git('init','-b','codex/deepseek-test');git('config','user.name','Synthetic Test');git('config','user.email','test@example.invalid');git('remote','add','origin','https://github.com/tonyluo2000/mile-commons.git');
 await mkdir(path.join(root,'lib'));await writeFile(path.join(root,'lib/average.mjs'),'export const average = values => values.reduce((a,b)=>a+b,0) / values.length;\n');git('add','.');git('commit','-m','synthetic source');
 const sha=git('rev-parse','HEAD');
 const manifest={schema:'cross-project.deepseek-implementation.v1',repository:'tonyluo2000/mile-commons',taskId:'average-empty-guard',title:'Guard empty arrays',instruction:'Return zero for an empty array.',baseSha:sha,headSha:sha,ownedPaths:['lib/average.mjs'],contextPaths:[],tests:[]};
 return {root,manifest,git};
}
test('mock explores exact selected source without provider calls or fabricated actual model',async t=>{
 const {root,manifest}=await fixture(t);let calls=0;
 const result=await runImplementation({root,manifest,providerCall:()=>{calls++;throw Error('must not call');}});
 assert.equal(calls,0);assert.equal(result.status,'MOCK_ONLY');assert.equal(result.actualModel,null);assert.equal(result.chargesUsd,null);
 assert.equal(result.gateEffect,'NONE');assert.ok(result.requestId);
});
test('validated proposal can modify exclusively owned source in clean isolated lane',async t=>{
 const {root,manifest}=await fixture(t);const prepared=await prepareImplementation({root,manifest});
 const proposal={summary:'Guarded an empty input.',changes:[{path:'lib/average.mjs',original_sha256:prepared.sources[0].sha256,content:'export const average = values => values.length ? values.reduce((a,b)=>a+b,0) / values.length : 0;\n'}]};
 const files=await applyImplementation({root,prepared,proposal});assert.deepEqual(files,['lib/average.mjs']);
 assert.match(await readFile(path.join(root,'lib/average.mjs'),'utf8'),/: 0/);
 await assert.rejects(applyImplementation({root,prepared,proposal}),/WORKTREE_NOT_CLEAN/);
});
test('rejects unowned paths, stale hashes, duplicate replacements and extra model commands',async t=>{
 const {root,manifest}=await fixture(t);const prepared=await prepareImplementation({root,manifest});
 const change={path:'lib/average.mjs',original_sha256:prepared.sources[0].sha256,content:'export const answer = 0;\n'};
 for(const proposal of [
  {summary:'test',changes:[{...change,path:'lib/other.mjs'}]},
  {summary:'test',changes:[{...change,original_sha256:'bad'}]},
  {summary:'test',changes:[change,change]},
  {summary:'test',changes:[change],command:'git push'}
 ]) assert.throws(()=>validateImplementationResponse(proposal,prepared));
});
test('rejects stale head, dirty source, symlinks and unapproved repository identity',async t=>{
 const {root,manifest,git}=await fixture(t);
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,headSha:'0'.repeat(40)}}),/STALE_HEAD/);
 await writeFile(path.join(root,'lib/average.mjs'),'owner uncommitted changes\n');
 await assert.rejects(prepareImplementation({root,manifest}),/UNCOMMITTED_SOURCE_CHANGE/);
 git('checkout','--','lib/average.mjs'); await symlink('average.mjs',path.join(root,'lib/link.mjs'));
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,ownedPaths:['lib/link.mjs']}}));
 git('remote','set-url','origin','https://github.com/other/repository.git');await assert.rejects(prepareImplementation({root,manifest}),/REPOSITORY_IDENTITY_MISMATCH/);
});
test('live mode refuses absent exact-call approval before provider and caps cost',async t=>{
 const {root,manifest}=await fixture(t);let calls=0;
 await assert.rejects(runImplementation({root,manifest,mode:'live',providerCall:()=>{calls++;}}),/EXACT_CALL_APPROVAL_REQUIRED/);
 assert.equal(calls,0);
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,maxCostUsd:1.01}}),/REQUEST_CAP_EXCEEDED/);
 await assert.rejects(prepareImplementation({root,manifest:{...manifest,tests:[{kind:'shell',files:['tests/x.py']}]}}),/INVALID_TESTS/);
});
test('worktree creation does not reset existing destinations or unrelated branches',async t=>{
 const {root,manifest}=await fixture(t);const destination=path.join(root,'lane');
 assert.equal(createIsolatedWorktree({root,destination,branch:'codex/deepseek-child',baseSha:manifest.headSha}),destination);
 assert.throws(()=>createIsolatedWorktree({root,destination,branch:'codex/deepseek-child',baseSha:manifest.headSha}));
});
test('concurrent owner edit between preflight and open is refused without overwrite',async t=>{
 const {root,manifest}=await fixture(t);const prepared=await prepareImplementation({root,manifest});
 const proposal={summary:'Bounded change.',changes:[{path:'lib/average.mjs',original_sha256:prepared.sources[0].sha256,content:'export const average = () => 0;\n'}]};
 await assert.rejects(applyImplementation({root,prepared,proposal,beforeOpen:()=>writeFile(path.join(root,'lib/average.mjs'),'owner concurrent edit\n')}),/SOURCE_CHANGED_DURING_APPLY/);
 assert.equal(await readFile(path.join(root,'lib/average.mjs'),'utf8'),'owner concurrent edit\n');
});
test('new owned files are allowed without granting unowned creation',async t=>{
 const {root,manifest}=await fixture(t);manifest.ownedPaths=['lib/empty-average.mjs'];
 const prepared=await prepareImplementation({root,manifest});assert.equal(prepared.sources[0].sha256,null);
 const proposal={summary:'Added a source helper.',changes:[{path:manifest.ownedPaths[0],original_sha256:null,content:'export const emptyAverage = 0;\n'}]};
 await applyImplementation({root,prepared,proposal});
 assert.equal(await readFile(path.join(root,manifest.ownedPaths[0]),'utf8'),proposal.changes[0].content);
});
