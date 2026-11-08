import { constants } from "node:fs";
import { lstat, open, realpath } from "node:fs/promises";
import path from "node:path";
import { containsRecognizedSecret, containsSuspiciousHighEntropy } from "./deepseek-source-scanner.mjs";

export const TRANSFER_POLICY_VERSION = "cross-project.source-transfer.v2";
// Eligibility is implemented for mock qualification, not live activation. An independently
// reviewed source change is required before this switch can change; CLI flags cannot do it.
export const LIVE_TRANSFER_ENABLED = false;
export function assertLiveTransferApproved() {
  if (!LIVE_TRANSFER_ENABLED) throw Object.assign(new Error("independent transfer-policy review and separate live activation are required"), { code: "POLICY_REVIEW_REQUIRED" });
}

const WEB = [".cjs", ".css", ".html", ".js", ".json", ".jsx", ".md", ".mjs", ".sh", ".sql", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml"];
const ROOT_COMMON = [".gitignore", ".nvmrc", "AGENTS.md", "CLAUDE.md", "README.md", "package.json", "package-lock.json", "tsconfig.json", "pyproject.toml", "requirements.txt"];
// Exact source-only routing configuration, never a config-directory wildcard.
const ROUTING_CONFIGURATION = ["config/ai-model-routing.json", "config/deepseek-toolchain.json", "config/model-project.json"];
const POLICIES = Object.freeze({
  "tonyluo2000/mile-commons": {
    roots: [...ROOT_COMMON, ...ROUTING_CONFIGURATION, "cloudflare-env.d.ts", "components.json", "drizzle.config.ts", "eslint.config.mjs", "next.config.ts", "postcss.config.mjs", "vite.config.ts", "mobile/App.tsx", "mobile/package.json", "mobile/package-lock.json", "mobile/app.json", "mobile/tsconfig.json", "mobile/babel.config.js", "mobile/metro.config.js"],
    prefixes: [".github/workflows/", ".claude/agents/", "app/", "auth0/", "cloudflare/", "components/", "db/", "docs/", "drizzle/", "examples/", "hooks/", "lib/", "scripts/", "tests/", "worker/"],
    extensions: WEB,
    native: [
      { prefix: "mobile/src/", extensions: [".ts", ".tsx"] },
      { prefix: "mobile/tests/", extensions: [".ts", ".tsx"] },
      { prefix: "mobile/__tests__/", extensions: [".ts", ".tsx"] },
      { prefix: "mobile/ios/MileCommons/", extensions: [".swift"] },
      { prefix: "mobile/ios/MileCommonsTests/", extensions: [".swift"] },
      { prefix: "mobile/android/app/src/main/java/com/milecommons/", extensions: [".kt"] },
      { prefix: "mobile/android/app/src/test/java/com/milecommons/", extensions: [".kt"] },
    ],
  },
  "briersystems/montefinance": {
    roots: [...ROOT_COMMON, ...ROUTING_CONFIGURATION, "pytest.ini", "frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json"],
    prefixes: ["backend/", "frontend/src/", "frontend/app/", "frontend/components/", "frontend/lib/", "scripts/", "tests/", "docs/", ".ai/deepseek/"],
    extensions: [...WEB, ".py"], native: [],
  },
  "tonyluo2000/explore-studio": {
    roots: [...ROOT_COMMON, ...ROUTING_CONFIGURATION, "LICENSE"],
    prefixes: ["engine/", "explore/", "scripts/", "tests/", "docs/", "classroom/my-world-template/", "course4teen-website/src/", "course4teen-website/app/", "course4teen-website/components/"],
    extensions: [...WEB, ".py"], native: [],
  },
});

const DENIED = [
  [/[^\x20-\x7e]|\\|:|%/, "non-canonical or escaped path"],
  [/(^|\/)\.env(?:\.|$)/i, "environment file"],
  [/(^|\/)(?:\.aws|\.ssh|credentials?|secrets?|signing)(?:[._/-]|$)/i, "credential directory or signing material"],
  [/(^|\/)(?:private[-_]?data|production[-_]?data|user[-_]?exports?|pii)(?:\/|$)/i, "private data directory"],
  [/^(?:docs\/evidence|tests\/fixtures|public\/uploads)(?:\/|$)/i, "high-risk evidence or fixture directory"],
  [/(^|\/)(?:data|datasets?|exports?|records?|production[-_]?logs?|logs?|photos?|images?|uploads?|gps[-_]?traces?|health[-_]?records?|financial[-_]?records?|learner[-_]?data|students|submissions|runner[-_]?data|customer[-_]?data|backups?|staging-backup)(?:\/|$)/i, "private records or media directory"],
  [/(^|\/)(?:node_modules|vendor|dist|build|generated|coverage|\.git|\.wrangler|\.next|\.gradle|Pods|DerivedData)(?:\/|$)/i, "generated artifact or dependency directory"],
  [/\.(?:key|pem|p12|pfx|jks|keystore|mobileprovision|cer|crt)$/i, "private key or certificate"],
  [/\.(?:db|sqlite\d?|csv|tsv|gpx|fit|tcx|har|log|png|jpe?g|gif|webp|heic|svg|pdf|zip|gz|bin|wasm|ipa|apk|aab|map)$/i, "extension is a binary, private export, media or generated artifact"],
];

export function projectPathPolicy(repository, filename) {
  if (typeof filename !== "string" || !filename || filename.startsWith("/") || filename.includes("\0")) return { allowed: false, reason: "invalid repository-relative path" };
  if (path.posix.normalize(filename) !== filename || filename === ".." || filename.startsWith("../") || filename.endsWith("/")) return { allowed: false, reason: "path traversal or non-canonical path" };
  for (const [pattern, reason] of DENIED) if (pattern.test(filename)) return { allowed: false, reason };
  if (containsRecognizedSecret(filename) || containsSuspiciousHighEntropy(filename)) return { allowed: false, reason: "credential-like value in path" };
  const policy = POLICIES[repository];
  if (!policy) return { allowed: false, reason: "repository is not approved" };
  if (policy.roots.includes(filename)) return { allowed: true, reason: null };
  const extension = path.posix.extname(filename).toLowerCase();
  const native = policy.native.find(rule => filename.startsWith(rule.prefix));
  if (native) return native.extensions.includes(extension) ? { allowed: true, reason: null } : { allowed: false, reason: "native extension is not allowlisted" };
  if (!policy.prefixes.some(prefix => filename.startsWith(prefix))) return { allowed: false, reason: "path is outside the source-review allowlist" };
  if (!policy.extensions.includes(extension)) return { allowed: false, reason: `extension ${extension || "(none)"} is not allowlisted` };
  return { allowed: true, reason: null };
}

// This only detects recognizable records. Human source classification and exact-call
// authorization remain mandatory: arbitrary private data cannot be proven absent by regex.
export function assertNoPrivateData(text) {
  // Public GitHub SSH remotes are protocol syntax, not private email. Only the
  // three approved repositories and the literal validated-source template are
  // recognized. Similar domains, ordinary addresses and arbitrary remotes stay
  // subject to the same personal-data denial below.
  const candidate = String(text).replace(/\bgit@github\.com:(?:\$\{(?:repository|task\.repository)\}|(?:tonyluo2000\/(?:mile-commons|explore-studio)|briersystems\/montefinance)(?:\.git)?)(?=["'`\s),\]])/g, "PUBLIC_GITHUB_SSH_REMOTE");
  const patterns = [
    /\b(?:latitude|longitude|lat|lng|heart[_-]?rate|blood[_-]?pressure|account[_-]?number|routing[_-]?number|social[_-]?security|ssn)["']?\s*[:=]\s*["']?-?\d+(?:\.\d+)?/i,
    /\b(?:runner|customer|learner|patient)[_-]?(?:name|email|record|address)["']?\s*[:=]\s*["'][^"'\n]+["']/i,
    /\b\d{3}-\d{2}-\d{4}\b/,
    /\b[A-Z0-9._%+-]+@(?!example\.(?:com|org|net)\b|localhost\b)[A-Z0-9.-]+\.[A-Z]{2,}\b/i,
  ];
  if (patterns.some(pattern => pattern.test(candidate))) throw Object.assign(new Error("recognizable personal, health, location or financial record is prohibited"), { code: "PRIVATE_DATA_DENIED" });
  if (String(text).includes("\0")) throw Object.assign(new Error("binary source is prohibited"), { code: "BINARY_SOURCE_DENIED" });
  return text;
}

export function assertSafeSource(repository, filename, text) {
  const policy = projectPathPolicy(repository, filename);
  if (!policy.allowed) throw Object.assign(new Error(policy.reason), { code: "PATH_POLICY_DENIED" });
  if (typeof text !== "string") throw new TypeError("source must be UTF-8 text");
  assertNoPrivateData(text);
  if (containsRecognizedSecret(text) || containsSuspiciousHighEntropy(text)) throw Object.assign(new Error("source contains a recognized secret or suspicious high-entropy value"), { code: "SOURCE_SECRET_DENIED" });
  return text;
}

export async function readSafeSource(root, repository, filename) {
  const policy = projectPathPolicy(repository, filename);
  if (!policy.allowed) throw Object.assign(new Error(policy.reason), { code: "PATH_POLICY_DENIED" });
  const absoluteRoot = path.resolve(root);
  if (await realpath(absoluteRoot) !== absoluteRoot || !(await lstat(absoluteRoot)).isDirectory()) throw Object.assign(new Error("repository root must be canonical and cannot contain symlinks"), { code: "SYMLINK_DENIED" });
  let current = absoluteRoot;
  for (const part of filename.split("/")) {
    current = path.join(current, part);
    const info = await lstat(current);
    if (info.isSymbolicLink()) throw Object.assign(new Error("source symlinks are prohibited"), { code: "SYMLINK_DENIED" });
  }
  const before = await lstat(current);
  if (!before.isFile() || before.size > 160_000) throw Object.assign(new Error("source must be a bounded regular file"), { code: "SOURCE_SIZE_DENIED" });
  const handle = await open(current, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const after = await handle.stat();
    if (after.ino !== before.ino || after.dev !== before.dev || await realpath(current) !== current) throw Object.assign(new Error("source changed while validating canonical path"), { code: "SOURCE_CHANGED" });
    const bytes = await handle.readFile();
    if (bytes.length > 160_000) throw Object.assign(new Error("source exceeds size bound"), { code: "SOURCE_SIZE_DENIED" });
    return assertSafeSource(repository, filename, new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } finally { await handle.close(); }
}
