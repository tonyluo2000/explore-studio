import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {realpathSync} from 'node:fs';
import path from 'node:path';
import {projectPathPolicy, assertNoPrivateData} from './deepseek-transfer-policy.mjs';

const PROJECTS = new Set(['tonyluo2000/mile-commons', 'briersystems/montefinance', 'tonyluo2000/explore-studio']);
const SHA = /^[a-f0-9]{40}$/;
const TOOLCHAIN_PATH = 'config/deepseek-toolchain.json';
const SELF_PATH = 'scripts/deepseek-source-classification.mjs';
const FIXTURE_PATH = 'tests/deepseek-transfer-policy.test.mjs';
const digest = value => createHash('sha256').update(value).digest('hex');
const fail = code => {throw Object.assign(new Error(code), {code});};

// These are exact, reviewed source words, not a pattern allowing uppercase
// strings, camelCase, arbitrary identifiers, or opaque tokens. They apply only
// to this tooling's explicit source paths below. Recognized secrets are never
// classified here and continue through the ordinary redaction/verification.
const SOURCE_WORDS = new Set([
  'reviewed-owner-record-required',
  'INDEPENDENT_POLICY_REVIEW_REQUIRED',
  'HIGH_REVIEW_OUTPUT_ENVELOPE_REQUIRED',
  'ABSOLUTE_EXTERNAL_OUTPUT_REQUIRED', 'INDEPENDENT_TRANSFER_POLICY_REVIEW_REQUIRED',
  'ISOLATED_DEEPSEEK_BRANCH_REQUIRED', 'SOURCE_CHANGED_SINCE_PREPARATION',
  'EXPLICIT_DEEPSEEK_PRO_MODEL_REQUIRED', 'EXPLICIT_DEEPSEEK_PRO_REQUEST_REQUIRED',
  'EXTERNAL_TRANSFER_AUTHORIZATION_REQUIRED', 'INDEPENDENT_SECURITY_REVIEW_REQUIRED',
  'INVALID_EXPLICIT_PROVIDER_REQUEST', 'PAID_CALL_AUTHORIZATION_REQUIRED',
  'INDEPENDENT_DIFFERENT_FAMILY_REVIEW_REQUIRED', 'EXISTING_RELEASE_CAPTAIN_REQUIRED',
  'GUARDED_DEEPSEEK_PROFILE_REQUIRED', 'PILOT_REQUIRES_ROUTINE_SYNTHETIC_TASK',
  'ROUTING_ACTIVATION_APPROVAL_REQUIRED', 'EXTERNAL_TRANSFER_NOT_ACKNOWLEDGED',
  'GITHUB_RUN_ID-GITHUB_RUN_ATTEMPT', 'PEAK_CACHE_MISS_PRICING_USD_PER_MILLION',
  'MOCK_ONLY_PENDING_REVIEW_AND_OWNER_ACTIVATION', 'PILOT_ONLY_PENDING_REVIEW_AND_OWNER_ACTIVATION',
  'codex-claude-default-deepseek-pro-explicit-owner-request-only',
  'codex-claude-primary-deepseek-pro-explicit-owner-request-only',
  'executeImplementationWithReceipt', 'estimatedMaximumCostPerAttemptUsd',
  'estimated_max_cost_per_attempt_usd',
  'proposal=validateImplementationResponse', 'lowThresholdPercent=configuration',
  'capabilities=discoverCapabilities', 'targetPrimary=ownerRequestedDeepSeek',
  'explicit-owner-request-only', 'before-task-cli-wrapper-only',
  'github-fine-grained-pat', 'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens',
  'PRIMARY_CAPACITY_OWNER_DECISION_REQUIRED', 'INVALID_TASK_AUTHORIZATION_SCOPE',
  'CALL_AUTHORIZATION_BODY_MISMATCH', 'CALL_AUTHORIZATION_EFFORT_MISMATCH',
  'CALL_AUTHORIZATION_REQUEST_MISMATCH', 'CALL_AUTHORIZATION_SCOPE_MISMATCH',
  'CALL_AUTHORIZATION_SPENDING_MISMATCH', 'SOURCE_TRANSFER_AUTHORIZATION_REQUIRED',
  'SOURCE_CLASSIFICATION_CONTEXT_INVALID', 'SOURCE_CLASSIFICATION_REPOSITORY_MISMATCH',
  'SOURCE_CLASSIFICATION_ROOT_UNSAFE', 'SOURCE_CLASSIFICATION_SECTION_MISMATCH',
  'SOURCE_DIGEST_REPOSITORY_MISMATCH', 'SOURCE_DIGEST_TARGET_NOT_REGULAR',
  'codex-claude-primary-deepseek-pro-task-scoped-owner-request-only',
  'fresh-task-scoped-owner-request-only', 'PAID_AUTHORIZATION_REPLAY_DENIED',
  'deepseek-review-cache-policy', 'classified=classificationContext',
  'remaining=containsRecognizedSecret', 'input_price_usd_per_million+receipt',
  'reported_usage_cost_upper_bound_usd=Math', 'independent_review_attested=false',
  'authorized_body_sha256=exactAuthorization', 'classified=classifyReviewSection',
]);
const TOOLING_PATHS = new Set([
  SELF_PATH, 'scripts/model-activation.mjs', 'tests/model-activation.test.mjs', 'scripts/deepseek-agent.mjs', 'scripts/deepseek-routing.mjs',
  'scripts/deepseek-review-core.mjs', 'scripts/deepseek-review.mjs',
  'scripts/deepseek-review-cache-policy.mjs',
  'scripts/deepseek-source-scanner.mjs', 'scripts/deepseek-transfer-policy.mjs',
  'scripts/deepseek-budget.mjs', 'scripts/agent-route.mjs', 'scripts/model-quality.mjs',
  'scripts/model-quota.mjs', 'scripts/model-capabilities.mjs', 'scripts/model-telemetry.mjs',
  'scripts/model-authorization.mjs', 'tests/model-authorization.test.mjs',
  'tests/deepseek-agent.test.mjs', 'tests/deepseek-routing.test.mjs', 'tests/deepseek-review.test.mjs',
  'tests/deepseek-budget.test.mjs', FIXTURE_PATH, 'tests/agent-route.test.mjs',
  'tests/model-quality.test.mjs', 'tests/model-quota.test.mjs', 'tests/model-telemetry.test.mjs',
  'tests/deepseek-source-classification.test.mjs', 'config/ai-model-routing.json', 'config/model-project.json', TOOLCHAIN_PATH,
]);

// SHA256 of the exact quoted source spans holding the pre-existing invented
// denial fixtures. Only these spans, in this one exact file, are redacted.
// A new fixture, a near match, a different path, or a changed raw section must
// pass ordinary scanning or receive a separately reviewed classification.
const SYNTHETIC_SPAN_HASHES = new Set([
  '24c060d7c5b321cc0d57fbfd637326a7e6071678464cad1f58df456fe52a5811',
  '9664199c6336866fdb4b40508defb5c26c186b1dd4e858f0fc9497e31f9e7e26',
  '2fbcfa47b4eb6584db281e2c97b109251a319bd66edabb5d9b4cfc27655b1974',
  'f77b11ec83af98335b39f9d3c5d491fe8e789c7904a3e24eecdd844e6a79e0b9',
  'dbc0edcb78ab538d0b626d79ca1937d32e090d277c6f6b47ee72a627bdc641f2',
  '32b5116b0f37a21685de6be4759c0eed97fc3c4ee21a47529fa90eb0faea643c',
  '585e2b028913b980b4fb593b75af4829ba24293cf73aeaab35455c49606ba253',
  'a190f00af47cae98261842a7b75a5ec1c2f3a52419ccacb6737721f01fa007f5',
  '44f95ad0586178c491a92e9715236b0c3b9d0453521ee334241f2984166d0dec',
  'ac21618954282d3a895313c9990f7839c37e652cbfaf0910585eda67ca5bcbfa',
  '832b7ed4a7866e7ddff31718649e7e58131ed799283295a8fddabe2597f7658a',
  // Exact synthetic prefixed-SSH-email denial template in the transfer test.
  'a8bcd630096328d1968629c7c5ee97aae208d9d495e293f9c8c75ae61aff4acf',
]);
// Existing git-test setup uses this one reserved synthetic identity. This is
// not permission for arbitrary addresses in tests, or a new email exception.
const GIT_TEST_IDENTITY_HASH = '86fc68d648ba6e53a652bcf21946cab2116f26d9e483409e1767caa323e6a0a0';
const GIT_TEST_PATHS = new Set(['tests/deepseek-agent.test.mjs', 'tests/agent-route.test.mjs']);
const REVIEW_TEST_PATH = 'tests/deepseek-review.test.mjs';
// Exact invented account-number denial literal in the context-forgery test.
const REVIEW_DENIAL_HASH = '8f7de0027218c582c71048deb1a3247aee79614d9f24a53382d4abdec9a933a6';

function git(root, args, bytes = false) {
  return execFileSync('git', ['-C', root, ...args], {encoding: bytes ? undefined : 'utf8',
    env: {...process.env, GIT_NO_REPLACE_OBJECTS: '1'}, timeout: 5000, maxBuffer: 2_000_000, stdio: ['ignore', 'pipe', 'pipe']});
}

function normalizeSection(section) {
  // GitHub may abbreviate object IDs differently. Normalize only those IDs;
  // the optional index-line mode remains part of the immutable comparison.
  return section.replace(/^index [a-f0-9]{7,64}\.\.[a-f0-9]{7,64}( [0-7]{6})?\n/m, (_match, mode = '') => `index NORMALIZED_OBJECT_IDS${mode}\n`)
    .replace(/\n?$/, '\n');
}

function verifySection({repository, filename, section, baseSha, headSha, root}) {
  if (!PROJECTS.has(repository) || !SHA.test(baseSha ?? '') || !SHA.test(headSha ?? '')
    || typeof root !== 'string' || typeof section !== 'string' || !projectPathPolicy(repository, filename).allowed) fail('SOURCE_CLASSIFICATION_CONTEXT_INVALID');
  const resolved = path.resolve(root);
  if (realpathSync(resolved) !== resolved) fail('SOURCE_CLASSIFICATION_ROOT_UNSAFE');
  const remote = git(resolved, ['remote', 'get-url', 'origin']).trim().replace(/\.git$/, '');
  if (![`https://github.com/${repository}`, `git@github.com:${repository}`].includes(remote)) fail('SOURCE_CLASSIFICATION_REPOSITORY_MISMATCH');
  git(resolved, ['merge-base', '--is-ancestor', baseSha, headSha]);
  const exactSection = git(resolved, ['diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--unified=3', baseSha, headSha, '--', filename]);
  if (!exactSection || normalizeSection(exactSection) !== normalizeSection(section)) fail('SOURCE_CLASSIFICATION_SECTION_MISMATCH');
  return resolved;
}

function replaceLiteralSpans(line, callback) {
  // A bounded lexer for quoted source spans, including template-source text.
  // No interpolation is executed or inferred safe: only exact known span
  // hashes qualify, and nested/unmatched templates receive no special trust.
  let result = '', cursor = 0;
  for (let index = 0; index < line.length; index++) {
    const quote = line[index];
    if (quote !== "'" && quote !== '"' && quote !== '`') continue;
    const start = index++;
    for (; index < line.length; index++) {
      if (line[index] === '\\') { index++; continue; }
      if (line[index] === quote) break;
    }
    if (index >= line.length) break;
    const literal = line.slice(start, index + 1);
    result += line.slice(cursor, start) + callback(literal);
    cursor = index + 1;
  }
  return result + line.slice(cursor);
}

function manifestAt(root, sha) {
  try {return JSON.parse(git(root, ['show', `${sha}:${TOOLCHAIN_PATH}`]));}
  catch {return null;}
}

function verifiedManifestDigest(root, repository, sha, filename, value) {
  // A matching blob digest does not classify a path's personal information.
  // Check the original target before its key can be masked in scanText.
  assertNoPrivateData(filename);
  const manifest = manifestAt(root, sha);
  if (manifest?.files?.[filename] !== value || !projectPathPolicy(repository, filename).allowed) fail('SOURCE_DIGEST_NOT_DECLARED');
  let bytes;
  const mode = git(root, ['ls-tree', sha, '--', filename]).match(/^([0-7]{6}) blob /)?.[1];
  if (!['100644', '100755'].includes(mode)) fail('SOURCE_DIGEST_TARGET_NOT_REGULAR');
  try {bytes = git(root, ['show', `${sha}:${filename}`], true);} catch {fail('SOURCE_DIGEST_TARGET_MISSING');}
  if (digest(bytes) !== value) fail('SOURCE_DIGEST_MISMATCH');
}

export function classifyReviewSection(context) {
  const root = verifySection(context);
  const {repository, filename, section, baseSha, headSha} = context;
  const counts = {};
  const bump = kind => {counts[kind] = (counts[kind] ?? 0) + 1;};
  let transmittedText = section;
  if (filename === FIXTURE_PATH || filename === REVIEW_TEST_PATH || GIT_TEST_PATHS.has(filename)) {
    transmittedText = section.split('\n').map(line => replaceLiteralSpans(line, literal => {
      const value = digest(literal);
      if (!(filename === FIXTURE_PATH && SYNTHETIC_SPAN_HASHES.has(value))
        && !(GIT_TEST_PATHS.has(filename) && value === GIT_TEST_IDENTITY_HASH)
        && !(filename === REVIEW_TEST_PATH && value === REVIEW_DENIAL_HASH)) return literal;
      bump('synthetic-denial-fixture');
      return `${literal[0]}[REDACTED:synthetic-denial-fixture]${literal[0]}`;
    })).join('\n');
  }
  let scanText = transmittedText;
  if (TOOLING_PATHS.has(filename)) {
    scanText = scanText.replace(/[A-Za-z0-9+/_=-]{12,}/g, token => {
      if (!SOURCE_WORDS.has(token)) return token;
      bump('known-source-word');
      return 'CLASSIFIED_SOURCE_WORD';
    });
  }
  if (filename === SELF_PATH) {
    scanText = scanText.split('\n').map(line => replaceLiteralSpans(line, literal => {
      const value = literal.slice(1, -1);
      if (!SYNTHETIC_SPAN_HASHES.has(value) && value !== GIT_TEST_IDENTITY_HASH && value !== REVIEW_DENIAL_HASH) return literal;
      bump('synthetic-span-digest');
      return `${literal[0]}CLASSIFIED_SPAN_DIGEST${literal[0]}`;
    })).join('\n');
  }
  if (filename === TOOLCHAIN_PATH) {
    const manifests = {LEFT: manifestAt(root, baseSha), RIGHT: manifestAt(root, headSha)};
    for (const manifest of Object.values(manifests)) {
      // The shared toolchain's provenance remains Mile Commons when vendored
      // into an adapter. Validation always hashes the current repository's own
      // immutable blobs, never another checkout's or the working tree's files.
      if (manifest && manifest.source_repository !== 'tonyluo2000/mile-commons') fail('SOURCE_DIGEST_REPOSITORY_MISMATCH');
    }
    scanText = scanText.split('\n').map(line => {
      const entry = line.match(/^([+ -])\s*"([^"\n]+)"\s*:\s*"([a-f0-9]{64})"[,]?$/);
      if (!entry) return line;
      const [, side, target, value] = entry;
      const sha = side === '-' ? baseSha : headSha;
      verifiedManifestDigest(root, repository, sha, target, value);
      if (side === ' ') verifiedManifestDigest(root, repository, baseSha, target, value);
      bump('verified-source-digest');
      return line.replace(value, 'CLASSIFIED_EXACT_SOURCE_DIGEST');
    }).join('\n');
    // File keys are exact manifest entries whose actual blob was verified.
    scanText = scanText.replace(/"([^"\n]+)"(?=\s*:\s*"CLASSIFIED_EXACT_SOURCE_DIGEST")/g, '"CLASSIFIED_SOURCE_PATH"');
  }
  if (['docs/operations/MODEL_ROUTING.md', SELF_PATH, 'tests/agent-route.test.mjs', 'tests/deepseek-routing.test.mjs', 'tests/deepseek-review.test.mjs', 'tests/deepseek-source-classification.test.mjs'].includes(filename)) {
    for (const link of [
      'https://github.com/tonyluo2000/mile-commons/issues/1120#issuecomment-6716279700',
      'https://github.com/briersystems/montefinance/issues/980#issuecomment-6716280037',
      'https://github.com/tonyluo2000/mile-commons/issues/1120#issuecomment-6715998366',
      'https://github.com/briersystems/montefinance/issues/980#issuecomment-6715998814',
      'https://github.com/tonyluo2000/mile-commons/issues/1120',
      'https://github.com/briersystems/montefinance/issues/980',
    ]) {
      scanText = scanText.replaceAll(link, (match, offset, input) => {
        const previous = input[offset - 1], next = input[offset + match.length];
        const beginsDiffLine = /(?:^|\n)[+-]$/.test(input.slice(0, offset));
        if (previous !== undefined && !/[\s"'`(\[]/.test(previous) && !beginsDiffLine
          || next !== undefined && !/[\s"'`\])]/.test(next)) return match;
        bump('public-policy-link');
        return 'CLASSIFIED_PUBLIC_POLICY_LINK';
      });
    }
  }
  return {scanText, transmittedText, counts};
}
