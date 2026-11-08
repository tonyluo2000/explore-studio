import assert from 'node:assert/strict';
import test from 'node:test';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync, realpathSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {classifyReviewSection} from '../scripts/deepseek-source-classification.mjs';
import {assertNoPrivateData, projectPathPolicy} from '../scripts/deepseek-transfer-policy.mjs';
import {containsRecognizedSecret, containsSuspiciousHighEntropy, redactSecrets} from '../scripts/deepseek-source-scanner.mjs';

const repository='tonyluo2000/mile-commons';
const hash=value=>createHash('sha256').update(value).digest('hex');
function fixture(t, files, initialFiles = {}) {
  const root=realpathSync(mkdtempSync(path.join(tmpdir(),'source-classification-')));
  t.after(()=>rmSync(root,{recursive:true,force:true}));
  const git=args=>execFileSync('git',['-C',root,'-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','-c','user.name=Synthetic','-c','user.email=fixture@example.com',...args],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trimEnd();
  git(['init','-q']); git(['remote','add','origin',`https://github.com/${repository}`]);
  writeFileSync(path.join(root,'README.md'),'Synthetic source classification test.\n');
  for(const [filename,content] of Object.entries(initialFiles)) {
    mkdirSync(path.dirname(path.join(root,filename)),{recursive:true});
    writeFileSync(path.join(root,filename),content);
  }
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

test('modified-file index mode cannot be forged or removed while normalizing hash abbreviations',t=>{
  const filename='scripts/deepseek-agent.mjs';
  const data=fixture(t,{[filename]:'export const value = 2;\n'},{[filename]:'export const value = 1;\n'});
  const context=data.context(filename);
  assert.match(context.section,/^index [a-f0-9]+\.\.[a-f0-9]+ 100644$/m);
  const abbreviated=context.section.replace(/^(index )[a-f0-9]+\.\.[a-f0-9]+/m,'$11111111..2222222');
  assert.doesNotThrow(()=>classifyReviewSection({...context,section:abbreviated}));
  for(const section of [
    context.section.replace(/^(index [^\n]+) 100644$/m,'$1 100755'),
    context.section.replace(/^(index [^\n]+) 100644$/m,'$1'),
  ]) assert.throws(()=>classifyReviewSection({...context,section}),{code:'SOURCE_CLASSIFICATION_SECTION_MISMATCH'});
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

test('the prefixed-SSH denial template has exact-file and exact-span synthetic classification',t=>{
  const fixtureSource=readFileSync(new URL('./deepseek-transfer-policy.test.mjs',import.meta.url),'utf8');
  const statement=fixtureSource.split('\n').find(line=>line.includes('`${prefix}git@'))+'\n';
  assert.ok(statement.length>40);
  const filename='tests/deepseek-transfer-policy.test.mjs';
  const data=fixture(t,{[filename]:statement,'tests/ordinary.test.mjs':statement});
  const classified=classifyReviewSection(data.context(filename));
  assert.equal(classified.counts['synthetic-denial-fixture'],1);
  assert.doesNotThrow(()=>assertNoPrivateData(classified.scanText));
  assert.throws(()=>assertNoPrivateData(classifyReviewSection(data.context('tests/ordinary.test.mjs')).scanText),{code:'PRIVATE_DATA_DENIED'});
  const near=fixture(t,{[filename]:statement.replace('${prefix}','${differentPrefix}')});
  const unclassified = classifyReviewSection(near.context(filename));
  assert.equal(unclassified.counts['synthetic-denial-fixture'],undefined);
  assert.throws(()=>assertNoPrivateData(unclassified.scanText),{code:'PRIVATE_DATA_DENIED'});
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

test('a verified blob digest cannot classify a private email embedded in its manifest target path',t=>{
  const filename='config/deepseek-toolchain.json',target=['scripts/runner','github.com.mjs'].join('@'),source='export const value = 42;\n';
  assert.equal(projectPathPolicy(repository,target).allowed,true);
  const manifest=JSON.stringify({source_repository:repository,files:{[target]:hash(source)}},null,2)+'\n';
  const data=fixture(t,{[filename]:manifest,[target]:source});
  assert.throws(()=>classifyReviewSection(data.context(filename)),{code:'PRIVATE_DATA_DENIED'});
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

test('unverified marker values cannot mask an email or opaque manifest key',t=>{
  const filename='config/deepseek-toolchain.json';
  const marker='CLASSIFIED_EXACT_SOURCE_DIGEST';
  const keys=[['scripts/runner','github.com.mjs'].join('@'),hash('synthetic unclassified manifest key')];
  for(const key of keys) {
    const manifest=JSON.stringify({source_repository:repository,files:{[key]:marker}},null,2)+'\n';
    const data=fixture(t,{[filename]:manifest});
    assert.throws(()=>classifyReviewSection(data.context(filename)),{code:'RAW_MARKER_DENIED'});
  }
});

test('raw marker injection is rejected in source, policy source and unrelated test files',t=>{
  const source='const payload = "CLASSIFIED_SOURCE_WORD";\n';
  for(const filename of ['scripts/deepseek-agent.mjs','scripts/deepseek-source-classification.mjs','tests/ordinary.test.mjs']) {
    const data=fixture(t,{[filename]:source});
    assert.throws(()=>classifyReviewSection(data.context(filename)),{code:'RAW_MARKER_DENIED'});
  }
});

test('a known marker definition is bound to its exact path and line without masking adjacent bytes',t=>{
  const filename='scripts/deepseek-source-classification.mjs';
  const policySource=readFileSync(new URL('../scripts/deepseek-source-classification.mjs',import.meta.url),'utf8');
  const definition=policySource.split('\n').find(line=>line.includes('CLASSIFIED' + '_SOURCE_WORD'));
  assert.ok(definition);
  const allowed=fixture(t,{[filename]:definition+'\n'});
  const context=allowed.context(filename),classified=classifyReviewSection(context);
  assert.equal(classified.transmittedText,context.section);
  assert.ok(classified.scanText.includes(definition));
  const wrongPath='scripts/deepseek-agent.mjs';
  const misplaced=fixture(t,{[wrongPath]:definition+'\n'});
  assert.throws(()=>classifyReviewSection(misplaced.context(wrongPath)),{code:'RAW_MARKER_DENIED'});
  const nearLine=fixture(t,{[filename]:definition+' const neighboring = 1;\n'});
  assert.throws(()=>classifyReviewSection(nearLine.context(filename)),{code:'RAW_MARKER_DENIED'});
});

test('classification policy and its tests retain full secret and private-data verification',t=>{
  const filenames=['scripts/deepseek-source-classification.mjs','tests/deepseek-source-classification.test.mjs'];
  const files=Object.fromEntries(filenames.map(filename=>[filename,readFileSync(new URL('../'+filename,import.meta.url),'utf8')]));
  const data=fixture(t,files);
  for(const filename of filenames) {
    const classified = classifyReviewSection(data.context(filename));
    assert.doesNotThrow(()=>assertNoPrivateData(classified.scanText));
    const redacted=redactSecrets(classified.scanText).text;
    assert.equal(containsRecognizedSecret(redacted),null);
    assert.equal(containsSuspiciousHighEntropy(redacted),false);
  }
});

test('new task-scoped policy labels and cache source names have finite exact classifications',t=>{
  const filename='config/ai-model-routing.json';
  const policy='codex-claude-primary-deepseek-pro-task-scoped-owner-request-only';
  const selection='fresh-task-scoped-owner-request-only';
  const cache='scripts/deepseek-review-cache-policy.mjs';
  const data=fixture(t,{[filename]:JSON.stringify({policy,selection})+'\n',[cache]:'const policy="deepseek-review-cache-policy";\n'});
  for(const file of [filename,cache]) {
    const context=data.context(file);
    const classified=classifyReviewSection(context);
    assert.equal(classified.transmittedText,context.section);
    assert.equal(containsSuspiciousHighEntropy(classified.scanText),false);
    assert.ok(classified.counts['known-source-word']>0);
  }
});

test('known source tokens do not authorize adjacent opaque values or waive credential redaction',t=>{
  const filename='scripts/deepseek-review-core.mjs';
  const source='const token="PAID_AUTHORIZATION_REPLAY_DENIED";\nconst label="deepseek-review-cache-policy'+ '-opaque";\n';
  const data=fixture(t,{[filename]:source});
  const classified=classifyReviewSection(data.context(filename));
  const redacted=redactSecrets(classified.transmittedText);
  assert.ok(Object.keys(redacted.counts).length>0);
  assert.ok(!redacted.text.includes('PAID_AUTHORIZATION_REPLAY_DENIED'));
  assert.equal(containsSuspiciousHighEntropy(classified.scanText),true);
});

test('only complete exact public policy URLs and finite known owner fragments are classified',t=>{
  const filename='docs/operations/MODEL_ROUTING.md';
  const links=[
    'https://github.com/tonyluo2000/mile-commons/issues/1120',
    'https://github.com/briersystems/montefinance/issues/980',
    'https://github.com/tonyluo2000/mile-commons/issues/1120#issuecomment-6716279700',
    'https://github.com/briersystems/montefinance/issues/980#issuecomment-6716280037',
    'https://github.com/tonyluo2000/mile-commons/issues/1120#issuecomment-6715998366',
    'https://github.com/briersystems/montefinance/issues/980#issuecomment-6715998814',
  ];
  const source=links.map(link=>`[Owner policy](${link})\n${link}\n`).join('');
  const data=fixture(t,{[filename]:source});
  const context=data.context(filename),classified=classifyReviewSection(context);
  assert.equal(classified.counts['public-policy-link'],links.length*2);
  assert.equal(classified.transmittedText,context.section);
});

test('policy URL prefixes cannot classify a different issue, an unknown fragment or an embedded URL',t=>{
  const filename='docs/operations/MODEL_ROUTING.md';
  const link='https://github.com/tonyluo2000/mile-commons/issues/1120';
  const source=[link+'9',link+'#unknown-fragment',link+'#issuecomment-6716279700'+'9','https://other.example.com/?next='+link].map(url=>`[Unclassified](${url})`).join('\n')+'\n';
  const data=fixture(t,{[filename]:source});
  const context=data.context(filename),classified=classifyReviewSection(context);
  assert.equal(classified.counts['public-policy-link'],undefined);
  assert.equal(classified.scanText,context.section);
  assert.equal(classified.transmittedText,context.section);
});
