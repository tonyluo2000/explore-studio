// Shared source scanner. Keep review redaction and implementation refusal consistent.
const SECRET_PATTERNS = [
  { kind: "private-key", pattern: /-----BEGIN [^-\n]*PRIVATE KEY-----[\s\S]*?-----END [^-\n]*PRIVATE KEY-----/g },
  { kind: "github-fine-grained-pat", pattern: /\bgithub_pat_[A-Za-z0-9_]{20,}\b/g },
  { kind: "github-token", pattern: /\bgh[pousr]_[A-Za-z0-9]{20,}\b/g },
  { kind: "slack-token", pattern: /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/g },
  { kind: "slack-webhook", pattern: /https:\/\/hooks\.slack\.com\/services\/[A-Za-z0-9/_-]{20,}/g },
  { kind: "stripe-key", pattern: /\b(?:[sr]k_(?:live|test)|whsec)_[A-Za-z0-9]{16,}\b/g },
  { kind: "npm-token", pattern: /\bnpm_[A-Za-z0-9]{20,}\b/g },
  { kind: "google-api-key", pattern: /\bAIza[A-Za-z0-9_-]{30,}\b/g },
  { kind: "openai-style-token", pattern: /\bsk-[A-Za-z0-9_-]{20,}\b/g },
  { kind: "aws-access-key", pattern: /\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/g },
  { kind: "jwt", pattern: /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g },
  { kind: "bearer-token", pattern: /(\bBearer[ \t]+)[A-Za-z0-9._~+\/-]{8,}/gi, replacement: "$1[REDACTED]" },
  { kind: "basic-auth-url", pattern: /(https?:\/\/)[^\s:/@]+:[^\s/@]+@/gi, replacement: "$1[REDACTED]@" },
  {
    kind: "quoted-assigned-secret",
    pattern: /((?:api[_-]?key|access[_-]?token|auth(?:orization|[_-]?token)?|client[_-]?secret|cookie|credential|pass(?:word)?|private[_-]?key|pwd|secret(?:[_-]?access[_-]?key)?|token)[ \t]*[=:][ \t]*)(["'])(?!\[REDACTED)([^\r\n]*?)\2/gi,
    replacement: "$1$2[REDACTED]$2",
  },
  {
    kind: "assigned-secret",
    pattern: /((?:api[_-]?key|access[_-]?token|auth(?:orization|[_-]?token)?|client[_-]?secret|cookie|credential|pass(?:word)?|private[_-]?key|pwd|secret(?:[_-]?access[_-]?key)?|token)[ \t]*[=:][ \t]*)(?!\[REDACTED)([^\s,;}{]+)/gi,
    replacement: "$1[REDACTED]",
  },
];

const SUSPICIOUS_TOKEN_PATTERN = /[A-Za-z0-9+/_=-]{32,}/g;
const KNOWN_NON_SECRET_LONG_VALUE = /^(?:[a-f0-9]{40}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|sha(?:256|384|512)-[A-Za-z0-9+/=]+)$/i;
export function redactSecrets(input) {
  let text = String(input ?? "");
  const counts = {};
  for (const entry of SECRET_PATTERNS) {
    let count = 0;
    text = text.replace(entry.pattern, (...parts) => {
      count += 1;
      if (entry.replacement) {
        return entry.replacement.replace(/\$(\d)/g, (_, digit) => parts[Number(digit)] ?? "");
      }
      return `[REDACTED:${entry.kind}]`;
    });
    if (count > 0) counts[entry.kind] = count;
  }
  return { text, counts };
}

export function containsRecognizedSecret(input) {
  const candidate = String(input ?? "").replace(/\[REDACTED(?::[a-z-]+)?\]/gi, "");
  for (const entry of SECRET_PATTERNS) {
    entry.pattern.lastIndex = 0;
    if (entry.pattern.test(candidate)) {
      entry.pattern.lastIndex = 0;
      return entry.kind;
    }
    entry.pattern.lastIndex = 0;
  }
  return null;
}

function tokenEntropy(value) {
  const frequencies = new Map();
  for (const character of value) frequencies.set(character, (frequencies.get(character) ?? 0) + 1);
  return [...frequencies.values()].reduce((sum, count) => {
    const probability = count / value.length;
    return sum - probability * Math.log2(probability);
  }, 0);
}

function isCompoundSourceName(candidate) {
  // '/' joins path/XML components; '_' and '-' join source-label words. The
  // old regex treated the whole concatenation as one opaque credential. Only
  // low-entropy words/numeric ids qualify; encoded or opaque components still
  // fail closed. This does not change any path allowlist or redaction rule.
  const components = candidate.split(/[/_-]/).filter(Boolean);
  return components.length > 1 && !/[+=]/.test(candidate)
    && (candidate.includes("/") || /[a-z][A-Z]/.test(candidate) || /^[a-z]+(?:_[a-z]+)+$/.test(candidate))
    && components.every(component => {
      if (component.length >= 32) return false;
      if (/^[0-9]+$/.test(component)) return tokenEntropy(component) <= 3.5;
      // Treat Pascal/camel-case source names as words too, without accepting
      // arbitrary mixed-case/base64 chunks (e.g. AbCdEfGh) as readable words.
      const words = component.split(/(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])/);
      return words.every(word => /^(?:[a-z]+|[A-Z]+|[A-Z][a-z]{2,})$/.test(word)
        && tokenEntropy(word.toLowerCase()) <= 3.5);
    });
}

export function containsSuspiciousHighEntropy(input) {
  const candidateText = String(input ?? "").replace(/\[REDACTED(?::[a-z-]+)?\]/gi, "");
  // These compound values can be shorter than the opaque-token threshold.
  // Check context before allowing public UUIDs or readable source names.
  for (const match of candidateText.matchAll(/[A-Za-z0-9+/_-]{12,}={0,2}/g)) {
    const candidate = match[0], prefix = candidateText.slice(Math.max(0, match.index - 200), match.index);
    const digits = candidate.split(/[/_-]/).filter(component => /^[0-9]+$/.test(component));
    if (digits.filter(component => component.length >= 6).length >= 2
      || /^[0-9_-]+$/.test(candidate) && candidate.replace(/[_-]/g, "").length >= 12) return true;
    const credential = /(?:^|[\s{,(])["']?(?:secret|token|password|passphrase|key|credential|auth)["']?\s*[=:]\s*["'`]?$/i.test(prefix);
    if (credential && KNOWN_NON_SECRET_LONG_VALUE.test(candidate)) return true;
    const quoted = /["'`]/.test(prefix.at(-1) ?? "") && candidateText[match.index + candidate.length] === prefix.at(-1);
    const assigned = /[=:]\s*["'`]?$/i.test(prefix);
    if ((quoted || assigned || credential) && digits.join("").length >= 12 && !KNOWN_NON_SECRET_LONG_VALUE.test(candidate)) return true;
    // Preserve symbolic error/diagnostic tags and reason/warning enums at
    // their source use sites, not arbitrary quoted/assigned snake_case values.
    const symbolic = /^[a-z]+(?:_[a-z]+){3,}$/.test(candidate)
      && /(?:\b(?:reject|fail|warnings\.add)\s*\(\s*|\b(?:reasons|warnings)\s*[:=]\s*\[[^\]\n]*|\bmessage\s*:\s*)["']$/.test(prefix);
    if (/^[a-z]+(?:[-_][a-z]+){3,}$/.test(candidate) && (credential || (quoted || assigned) && !symbolic)) return true;
    if (/^[a-f0-9]+(?:-[a-f0-9]+)+$/i.test(candidate) && candidate.replace(/-/g, "").length >= 32
      && !KNOWN_NON_SECRET_LONG_VALUE.test(candidate)) return true;
  }
  for (const match of candidateText.matchAll(SUSPICIOUS_TOKEN_PATTERN)) {
    const candidate = match[0];
    if (KNOWN_NON_SECRET_LONG_VALUE.test(candidate)) continue;
    if (tokenEntropy(candidate) >= 3.5 && !isCompoundSourceName(candidate)) return true;
  }
  return false;
}

