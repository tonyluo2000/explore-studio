import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import { mkdtemp, mkdir, symlink, writeFile, rm, realpath } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";
import { projectPathPolicy, assertSafeSource, readSafeSource, assertLiveTransferApproved, assertNoPrivateData } from "../scripts/deepseek-transfer-policy.mjs";
import {redactSecrets, containsRecognizedSecret, containsSuspiciousHighEntropy} from "../scripts/deepseek-source-scanner.mjs";
import { prepareReviewInput, runReview, callDeepSeek, createDeepSeekTestClient, prepareDeepSeekRequest } from "../scripts/deepseek-review-core.mjs";
const MC = "tonyluo2000/mile-commons", MF = "briersystems/montefinance", ES = "tonyluo2000/explore-studio";
const diff = (file, value="export const value = 2;") => `diff --git a/${file} b/${file}\nindex 1111111..2222222 100644\n--- a/${file}\n+++ b/${file}\n@@ -1 +1 @@\n-export const value = 1;\n+${value}\n`;
const constrainedQuota = () => Object.fromEntries(["codex","claude"].map(family=>[family,{state:"low",source:"owner",observedAt:new Date().toISOString(),expiresAt:new Date(Date.now()+3_600_000).toISOString()}]));
const inventory = file => [{ filename: file, additions: 1, deletions: 1 }];
function transportScope(messages=[]) {
  const repository=MC,baseSha="a".repeat(40),headSha="b".repeat(40),requestId="c".repeat(64);
  const budgetIdentity={repository,taskId:"scope-test",taskType:"implementation",baseSha,headSha,provider:"deepseek",actualModel:"deepseek-v4-pro",requestId,reasoningEffort:"low",authorizationId:"owner-test-0001"};
  const ownerRequest={schema:"cross-project.deepseek-owner-request.v1",authorizationId:"owner-test-0001",repository,taskId:"scope-test",role:"implementation",baseSha,headSha,model:"deepseek-v4-pro",issuedAt:new Date().toISOString(),expiresAt:new Date(Date.now()+3_600_000).toISOString(),authorizationReference:"owner:test"};
  const body=prepareDeepSeekRequest({model:"deepseek-v4-pro",messages,reasoningEffort:"low",maxCostUsd:1}).serializedBody;
  const callAuthorization={...ownerRequest,schema:"cross-project.deepseek-call-authorization.v1",requestId,bodySha256:createHash("sha256").update(body).digest("hex"),reasoningEffort:"low",maxCostUsd:1,transferApproved:true,paymentApproved:true};
  return {budgetIdentity,ownerRequest,callAuthorization,reasoningEffort:"low"};
}

test("only the three exact routing configuration paths become eligible",()=>{
  for(const repository of [MC,MF,ES]) {
    for(const file of ["config/ai-model-routing.json","config/deepseek-toolchain.json","config/model-project.json"]) assert.equal(projectPathPolicy(repository,file).allowed,true);
    for(const file of ["config/other.json","config/ai-model-routing.json.bak","config/deepseek-toolchain.json/key.json","config/private-data/ai-model-routing.json","config/.env","config/credentials.json","config/model-project.json/../other.json"]) assert.equal(projectPathPolicy(repository,file).allowed,false);
  }
});

test("only Mile Commons' exact existing DeepSeek workflow is eligible",()=>{
  const workflow=".github/workflows/deepseek-review.yml";
  assert.equal(projectPathPolicy(MC,workflow).allowed,true);
  for(const repository of [MF,ES]) assert.equal(projectPathPolicy(repository,workflow).allowed,false);
  for(const repository of [MC,MF,ES]) for(const filename of [
    ".github/workflows/other.yml", ".github/workflows/deepseek-review.yaml",
    ".github/workflows/deepseek-review.yml.bak", ".github/workflows/deepseek-review-production.yml",
    ".github/workflows/production.yml", ".github/workflows/deepseek-review.yml/production.yml",
    ".github/workflows/nested/deepseek-review.yml", ".github/workflows/DeepSeek-review.yml",
    ".github/workflows/../workflows/deepseek-review.yml", ".github/workflows/.env",
  ]) assert.equal(projectPathPolicy(repository,filename).allowed,false,`${repository}:${filename}`);
});

test("public approved GitHub SSH protocol syntax is not private email, near matches still fail",()=>{
  for(const repository of [MC,MF,ES]) assert.doesNotThrow(()=>assertNoPrivateData(`const remote = 'git@github.com:${repository}.git';`));
  assert.doesNotThrow(()=>assertNoPrivateData('const remote = `git@github.com:${repository}`;'));
  for(const text of ['git@github.com.evil','git@github.com:other/repository','alice@private-domain.com']) assert.throws(()=>assertNoPrivateData(text),{code:"PRIVATE_DATA_DENIED"});
  for(const prefix of ['name.','name+','name-','name_','name%','name0']) {
    assert.throws(()=>assertNoPrivateData(`${prefix}git@github.com:${MC}`),{code:"PRIVATE_DATA_DENIED"});
  }
});

test("redaction sentinels retain expression boundaries without hiding nearby real credentials",()=>{
  for(const text of ['Authorization: `Bearer ${apiKey}`','token: process.env.TOKEN ?? ""','apiKey: apiKey ? apiKey.trim() : undefined','const apiKey = options.apiKey || process.env.DEEPSEEK_API_KEY;']) {
    const redacted=redactSecrets(text);
    assert.ok(Object.keys(redacted.counts).length);
    assert.equal(containsRecognizedSecret(redacted.text),null);
  }
  for(const text of ['token=[REDACTED]still-present-value','token="[REDACTED]still-present-value"','token=[REDACTED-near-match]','[REDACTED] ' + 'gh' + 'p_' + 'abcdefghijklmnopqrstuvwxyz' + '123456']) assert.notEqual(containsRecognizedSecret(text),null);
  assert.equal(containsSuspiciousHighEntropy('AbCdEfGhIjKlMnOp[REDACTED]QrStUvWxYz01234'),false);
});

test("project adapters permit source and exact native config without blanket mobile eligibility", () => {
  for (const file of ["mobile/App.tsx", "mobile/package-lock.json", "mobile/src/workouts/sync.ts", "mobile/ios/MileCommons/Sync.swift", "mobile/android/app/src/main/java/com/milecommons/Sync.kt"]) assert.equal(projectPathPolicy(MC,file).allowed,true,file);
  for (const file of ["mobile/other.ts", "mobile/ios/Other/App.swift", "mobile/android/app/build.gradle", "mobile/assets/photo.jpg", "mobile/src/app.json", "mobile/src/customer/export.json"]) assert.equal(projectPathPolicy(MC,file).allowed,false,file);
  assert.equal(projectPathPolicy(MF,"backend/domain/scenarios/service.py").allowed,true);
  assert.equal(projectPathPolicy(ES,"explore/curriculum/missions.py").allowed,true);
  assert.equal(projectPathPolicy(ES,"students/alice/course.py").allowed,false);
  assert.equal(projectPathPolicy("unapproved/repo","scripts/example.mjs").allowed,false);
});

test("private, generated, binary and disguised noncanonical paths always fail closed", () => {
  for (const repository of [MC, MF, ES]) for (const file of ["scripts/.env.local", "scripts/credentials/key.json", "scripts/health-records/alice.json", "tests/fixtures/export.json", "docs/financial-records/data.json", "scripts/logs/production.txt", "scripts/build/bundle.js", "scripts/a.sqlite", "scripts/account.csv", "scripts/x/../safe.js", "scripts\\safe.js", "scripts/%2e%2e/safe.js", "scripts/public/photo.png", "scripts/signing/release.json"]) assert.equal(projectPathPolicy(repository,file).allowed,false,`${repository}:${file}`);
});

test("implementation scanner refuses credentials, entropy and recognizable private records", () => {
  assert.equal(assertSafeSource(MC,"lib/source.ts","export const value = 42;"),"export const value = 42;");
  for (const text of ['const token="' + 'gh' + 'p_' + 'abcdefghijklmnopqrstuvwxyz' + '123456";', 'const opaque="AbCdEfGhIjKlMnOpQrStUvWxYz0123456789_+";', '{"latitude":40.7128,"longitude":-74.0060}', '{"heart_rate":151}', '{"account_number":"123456789"}', '{"learner_name":"Alice"}', 'const contact="alice@private-domain.com";', 'binary\0payload']) assert.throws(()=>assertSafeSource(MC,"lib/source.ts",text), /prohibited|secret|entropy/);
});

test("native diff preflight preserves complete accounting and refuses mixed restricted files", () => {
  assert.deepEqual(prepareReviewInput({repository:MC,diff:diff("mobile/App.tsx"),files:inventory("mobile/App.tsx")}).files,["mobile/App.tsx"]);
  assert.throws(()=>prepareReviewInput({repository:MC,diff:diff("mobile/App.tsx")+diff("mobile/private-data/runner.json"),files:[...inventory("mobile/App.tsx"),...inventory("mobile/private-data/runner.json")]}),error=>error.code==="PATH_POLICY_DENIED");
  assert.throws(()=>prepareReviewInput({repository:MC,diff:diff("mobile/App.tsx"),files:[...inventory("mobile/App.tsx"),...inventory("mobile/package-lock.json")]}),/inventory mismatch/);
  assert.throws(()=>prepareReviewInput({repository:MC,diff:diff("lib/source.ts",'{"latitude":40.7128}'),files:inventory("lib/source.ts")}),error=>error.code==="PRIVATE_DATA_DENIED");
});

test("symlink modes and reclassified rename sources cannot enter review payload", () => {
  assert.throws(()=>prepareReviewInput({diff:diff("lib/source.ts").replace("100644","120000"),files:inventory("lib/source.ts")}),error=>error.code==="SYMLINK_DENIED");
  assert.throws(()=>prepareReviewInput({diff:diff("lib/source.ts").replace("--- a/lib/source.ts","--- a/.env.local"),files:inventory("lib/source.ts")}),error=>error.code==="PATH_POLICY_DENIED");
});

test("local reads reject final and parent symlinks and return bounded UTF8 source", async () => {
  const root = await realpath(await mkdtemp(path.join(tmpdir(),"deepseek-path-policy-")));
  try {
    await mkdir(path.join(root,"lib")); await writeFile(path.join(root,"lib","safe.ts"),"export const safe = true;");
    assert.equal(await readSafeSource(root,MC,"lib/safe.ts"),"export const safe = true;");
    await symlink("safe.ts",path.join(root,"lib","link.ts"));
    await assert.rejects(readSafeSource(root,MC,"lib/link.ts"),error=>error.code==="SYMLINK_DENIED");
    await symlink("lib",path.join(root,"scripts"));
    await assert.rejects(readSafeSource(root,MC,"scripts/safe.ts"),error=>error.code==="SYMLINK_DENIED");
    await writeFile(path.join(root,"lib","large.ts"),"x".repeat(160001));
    await assert.rejects(readSafeSource(root,MC,"lib/large.ts"),error=>error.code==="SOURCE_SIZE_DENIED");
  } finally { await rm(root,{recursive:true,force:true}); }
});

test("new policy has no CLI live activation and denies before provider or budget access", async () => {
  assert.throws(assertLiveTransferApproved,error=>error.code==="POLICY_REVIEW_REQUIRED");
  let fetches=0,budgets=0;
  await assert.rejects(callDeepSeek({apiKey:"offline-key",model:"deepseek-v4-pro",repository:MC,...transportScope(),routingContext:{risk:"low",complexity:"routine"},messages:[],maxCostUsd:1,fetchImpl:async()=>{fetches++;},budgetCall:async()=>{budgets++;}}),error=>error.code==="POLICY_REVIEW_REQUIRED");
  assert.equal(fetches,0); assert.equal(budgets,0);
  assert.throws(()=>prepareDeepSeekRequest({model:"deepseek-flash",messages:[],maxCostUsd:1.01}),/no more than 1/);
  assert.equal(prepareDeepSeekRequest({model:"deepseek-flash",messages:[]}).requestBody.reasoning_effort,"low");
});

test("private PR metadata denies even an otherwise eligible complete diff", async () => {
  const head="a".repeat(40), base="b".repeat(40); let calls=0;
  const result=await runReview({repository:MC,pullNumber:1,headSha:head,mode:"mock",github:{getPull:async()=>({state:"open",head:{sha:head},base:{sha:base},title:'Runner record: {"runner_name":"Alice"}'}),getComparison:async()=>({complete:true,baseSha:base,headSha:head,mergeBaseSha:base,status:"ahead",totalCommits:1,files:inventory("lib/source.ts"),diff:diff("lib/source.ts")})},providerCall:async()=>{calls++;}});
  assert.equal(result.errors[0].code,"PRIVATE_DATA_DENIED"); assert.equal(calls,0); assert.equal(result.review_status,"REVIEW_NOT_COMPLETE");
});


test("request-body binding fails before activation, ledger or transport", async () => {
  let fetches = 0;
  const messages=[{role:"user",content:"bounded json request"}];
  const options = { apiKey: "offline-key", repository: MC, model: "deepseek-v4-pro", ...transportScope(messages), routingContext: { quota: constrainedQuota(), risk: "low", complexity: "routine" }, messages, maxCostUsd: 1, expectedBodySha256: "f".repeat(64), fetchImpl: async () => { fetches++; }, assertTransferApproved: () => {}, budgetCall: async (_policy, callback) => callback() };
  await assert.rejects(callDeepSeek(options), {code:"REQUEST_BODY_HASH_MISMATCH"});
  assert.equal(fetches, 0);
  const fakeClient = createDeepSeekTestClient({fetchImpl:options.fetchImpl});
  await assert.rejects(fakeClient(options), {code:"REQUEST_BODY_HASH_MISMATCH"});
  assert.equal(fetches, 0);
});

test("offline test-client construction requires runner context and a fake transport", () => {
  assert.throws(()=>createDeepSeekTestClient({fetchImpl:fetch}), {code:"TEST_CLIENT_CONTEXT_REQUIRED"});
  const context = process.env.NODE_TEST_CONTEXT;
  try {
    delete process.env.NODE_TEST_CONTEXT;
    assert.throws(()=>createDeepSeekTestClient({fetchImpl:async()=>{}}), {code:"TEST_CLIENT_CONTEXT_REQUIRED"});
  } finally { if (context === undefined) delete process.env.NODE_TEST_CONTEXT; else process.env.NODE_TEST_CONTEXT = context; }
});
