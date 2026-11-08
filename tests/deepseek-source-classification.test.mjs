import assert from 'node:assert/strict';
import test from 'node:test';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync, realpathSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {classifyReviewSection} from '../scripts/deepseek-source-classification.mjs';
import {assertNoPrivateData} from '../scripts/deepseek-transfer-policy.mjs';
import {containsRecognizedSecret, containsSuspiciousHighEntropy, redactSecrets} from '../scripts/deepseek-source-scanner.mjs';

const repository='tonyluo2000/mile-commons';
const hash=value=>createHash('sha256').update(value).digest('hex');
function fixture(t, files) {
  const root=realpathSync(mkdtempSync(path.join(tmpdir(),'source-classification-')));
  t.after(()=>rmSync(root,{recursive:true,force:true}));
  const git=args=>execFileSync('git',['-C',root,'-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','-c','user.name=Synthetic','-c','user.email=fixture@example.com',...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trimEnd();
  git(['init','-q']); git(['remote','add','origin',`https://github.com/${repository}`]);
  writeFileSync(path.join(root,'README.md'),'Synthetic source classification test.\n');
  git(['add','.']); git(['commit','-qm','Synthetic base']);
  const baseSha=git(['rev-parse','HEAD']);
  for(const [filename,content] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(root,filename)),{recursive:true});
    writeFileSync(path.join(root,filename),content);
  }
  git(['add','.']); git(['commit','-qm','Synthetic source delta']);
  const headSha=git(['rev-parse','HEAD']);
  const context=filename=>({repository,filename,root,baseSha,headSha,
    section:git(['diff','--no-ext-diff','--no-textconv','--no-renames','--unified=3',baseSha,headSha,'--',filename])+'\n'});
  return {root,git,baseSha,headSha,context};
}

test('exact immutable comparison permits a finite known source word without omitting it from payload',t=>{
  const filename='scripts/deepseek-agent.mjs';
  const source='throw new Error("ISOLATED_DEEPSEEK_BRANCH_REQUIRED");\n';
  const data=fixture(t,{[filename]:source});
  const context=data.context(filename);
  const result=classifyReviewSection(context);
  assert.ok(result.scanText.includes('CLASSIFIED_SOURCE_WORD'));
  assert.equal(result.transmittedText,context.section);
  assert.equal(result.counts['known-source-word'],1);
  assert.equal(containsSuspiciousHighEntropy(result.scanText),false);
});

test('different repository, stale section, missing identity and near-match opaque words cannot be waived',t=>{
  const filename='scripts/deepseek-agent.mjs';
  const source='throw new Error("ISOLATED_DEEPSEEK_BRANCH_REQUIRED'+ '-NEAR-MATCH");\n';
  const data=fixture(t,{[filename]:source});
  const context=data.context(filename);
  const result=classifyReviewSection(context);
  assert.equal(result.scanText,context.section);
  assert.equal(containsSuspiciousHighEntropy(result.scanText),true);
  assert.throws(()=>classifyReviewSection({...context,repository:'briersystems/montefinance'}),{code:'SOURCE_CLASSIFICATION_REPOSITORY_MISMATCH'});
  assert.throws(()=>classifyReviewSection({...context,section:context.section.replace('NEAR-MATCH','DIFFERENT')}),{code:'SOURCE_CLASSIFICATION_SECTION_MISMATCH'});
  assert.throws(()=>classifyReviewSection({...context,baseSha:undefined}),{code:'SOURCE_CLASSIFICATION_CONTEXT_INVALID'});
});

test('index abbreviation may vary while every source byte, mode and hunk remains bound',t=>{
  const filename='scripts/deepseek-agent.mjs';
  const data=fixture(t,{[filename]:'export const value = 42;\n'});
  const context=data.context(filename);
  const abbreviated=context.section.replace(/^index [a-f0-9]+\.\.[a-f0-9]+/m,'index 1111111..2222222');
  assert.doesNotThrow(()=>classifyReviewSection({...context,section:abbreviated}));
  assert.throws(()=>classifyReviewSection({...context,section:context.section.replace('100644','120000')}),{code:'SOURCE_CLASSIFICATION_SECTION_MISMATCH'});
  assert.throws(()=>classifyReviewSection({...context,section:context.section.replace('42','43')}),{code:'SOURCE_CLASSIFICATION_SECTION_MISMATCH'});
});

test('only exact known synthetic spans in the exact fixture path are redacted',t=>{
  const fixtureSource=readFileSync(new URL('./deepseek-transfer-policy.test.mjs',import.meta.url),'utf8');
  const denialStatement=fixtureSource.split('\n').find(line=>line.includes('for (const text of')&&line.includes('lib/source.ts'))+'\n';
  assert.ok(denialStatement.length>100);
  const filename='tests/deepseek-transfer-policy.test.mjs';
  const data=fixture(t,{[filename]:denialStatement,'tests/ordinary.test.mjs':denialStatement});
  const classified=classifyReviewSection(data.context(filename));
  assert.ok(classified.counts['synthetic-denial-fixture']>=6);
  assert.doesNotThrow(()=>assertNoPrivateData(classified.scanText));
  const ordinary=classifyReviewSection(data.context('tests/ordinary.test.mjs'));
  assert.equal(ordinary.counts['synthetic-denial-fixture'],undefined);
  assert.throws(()=>assertNoPrivateData(ordinary.scanText),{code:'PRIVATE_DATA_DENIED'});
});

test('a near-match fixture or real-looking private record remains prohibited in an eligible source file',t=>{
  const fixtureSource=readFileSync(new URL('./deepseek-transfer-policy.test.mjs',import.meta.url),'utf8');
  const denialStatement=fixtureSource.split('\n').find(line=>line.includes('for (const text of')&&line.includes('lib/source.ts'))+'\n';
  const filename='tests/deepseek-transfer-policy.test.mjs';
  const data=fixture(t,{[filename]:denialStatement.replace('40.7128','40.7129')});
  const classified=classifyReviewSection(data.context(filename));
  assert.throws(()=>assertNoPrivateData(classified.scanText),{code:'PRIVATE_DATA_DENIED'});
});

test('toolchain source digest is verified against exact-head blob and stays visible in review payload',t=>{
  const filename='config/deepseek-toolchain.json',target='scripts/deepseek-agent.mjs',source='export const value = 42;\n';
  const value=hash(source);
  const manifest=JSON.stringify({source_repository:repository,files:{[target]:value}},null,2)+'\n';
  const data=fixture(t,{[filename]:manifest,[target]:source});
  const context=data.context(filename);
  const classified=classifyReviewSection(context);
  assert.equal(classified.counts['verified-source-digest'],1);
  assert.ok(classified.transmittedText.includes(value));
  assert.ok(!classified.scanText.includes(value));
  assert.equal(containsSuspiciousHighEntropy(classified.scanText),false);
  writeFileSync(path.join(data.root,target),'Uncommitted replacement is irrelevant.\n');
  assert.doesNotThrow(()=>classifyReviewSection(context));
});

test('forged manifest digest and arbitrary opaque hex in ordinary source remain blocked',t=>{
  const filename='config/deepseek-toolchain.json',target='scripts/deepseek-agent.mjs',source='export const value = 42;\n';
  const unknown=hash('unclassified opaque source token');
  const manifest=JSON.stringify({source_repository:repository,files:{[target]:unknown}},null,2)+'\n';
  const data=fixture(t,{[filename]:manifest,[target]:`const opaque="${unknown}";\n`});
  assert.throws(()=>classifyReviewSection(data.context(filename)),{code:'SOURCE_DIGEST_MISMATCH'});
  const classified=classifyReviewSection(data.context(target));
  assert.ok(classified.scanText.includes(unknown));
  assert.equal(containsSuspiciousHighEntropy(redactSecrets(classified.scanText).text),true);
});

test('classification policy constants themselves retain full secret and private-data verification',t=>{
  const filename='scripts/deepseek-source-classification.mjs';
  const source=readFileSync(new URL('../scripts/deepseek-source-classification.mjs',import.meta.url),'utf8');
  const data=fixture(t,{[filename]:source});
  const classified=classifyReviewSection(data.context(filename));
  assert.doesNotThrow(()=>assertNoPrivateData(classified.scanText));
  const redacted=redactSecrets(classified.scanText).text;
  assert.equal(containsRecognizedSecret(redacted),null);
  assert.equal(containsSuspiciousHighEntropy(redacted),false);
});
