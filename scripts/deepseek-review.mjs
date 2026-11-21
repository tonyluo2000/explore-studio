#!/usr/bin/env node
import { mkdir, writeFile, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  DEFAULT_MAX_DIFF_CHARS,
  DEFAULT_MAX_OUTPUT_TOKENS,
  DEFAULT_MAX_REQUEST_BYTES,
  DEFAULT_MODEL,
  DEFAULT_PROVIDER_RETRIES,
  redactSecrets,
  runReviewWithState,
  validateHeadSha,
  validateModel,
  validateReservationId,
  validateRepository,
} from "./deepseek-review-core.mjs";

const USAGE = `Usage:
  node scripts/deepseek-review.mjs --repo OWNER/REPO --pr NUMBER --head EXACT_40_CHAR_SHA [options]

Modes:
  --mock                               Default. Fetch, validate, redact, and build evidence without calling DeepSeek.
  --live                               Call the official DeepSeek API. Requires both the acknowledgement and API key.
  --acknowledge-external-transfer      Confirms allowlisted, redacted source will leave GitHub for DeepSeek.

Options:
  --model MODEL                        deepseek-v4-pro (explicit owner request only)
  --routing-context FILE               Operator choice: ownerRequestedDeepSeek=true and implementer family
  --reasoning-effort low|high           Optional effort override; cannot lower risk requirements
  --max-diff-chars NUMBER              Default: ${DEFAULT_MAX_DIFF_CHARS}
  --max-output-tokens NUMBER           Default: ${DEFAULT_MAX_OUTPUT_TOKENS}; maximum: 16000
  --max-request-bytes NUMBER           Default: ${DEFAULT_MAX_REQUEST_BYTES}; serialized UTF-8 body ceiling
  --provider-retries NUMBER            Must be 0; automatic provider retries are prohibited
  --max-cost-usd NUMBER                Required in live mode; conservative peak-price ceiling
  --base EXACT_40_CHAR_SHA             Pin the PR base used by cache, receipt, and comparison
  --reserve-only                       Complete preflight and reserve one attempt without calling DeepSeek
  --reservation-id RUN_ID-RUN_ATTEMPT  Trusted GitHub Actions identity for --reserve-only
  --resume-reservation ID              Resume only the exact durably persisted reservation
  --output PATH                        Default: outputs/deepseek-review/report.json
  --state-dir PATH                     Default: outputs/deepseek-review/state
  --help

Environment:
  GH_TOKEN or GITHUB_TOKEN             Optional for public repositories; required when GitHub access needs authentication.
  DEEPSEEK_API_KEY                     Required only in live mode. Never logged or written to evidence.
`;

function parseInteger(value, label) {
  if (!/^\d+$/.test(value ?? "")) throw new Error(`${label} must be an integer`);
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1) throw new Error(`${label} must be a positive safe integer`);
  return parsed;
}

function parseNonNegativeInteger(value, label) {
  if (!/^\d+$/.test(value ?? "")) throw new Error(`${label} must be a non-negative integer`);
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) throw new Error(`${label} must be a non-negative safe integer`);
  return parsed;
}

function parsePositiveNumber(value, label) {
  if (!/^\d+(?:\.\d+)?$/.test(value ?? "")) throw new Error(`${label} must be a positive number`);
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) throw new Error(`${label} must be a positive number`);
  return parsed;
}

export function parseArgs(argv) {
  const options = {
    repository: process.env.GITHUB_REPOSITORY,
    model: DEFAULT_MODEL,
    mode: "mock",
    acknowledgeExternalTransfer: false,
    maxDiffChars: DEFAULT_MAX_DIFF_CHARS,
    maxOutputTokens: DEFAULT_MAX_OUTPUT_TOKENS,
    maxRequestBytes: DEFAULT_MAX_REQUEST_BYTES,
    providerRetries: DEFAULT_PROVIDER_RETRIES,
    maxCostUsd: null,
    output: "outputs/deepseek-review/report.json",
    stateDirectory: "outputs/deepseek-review/state",
    reserveOnly: false,
  };
  let selectedMode = null;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const take = () => {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error(`${argument} requires a value`);
      index += 1;
      return value;
    };
    if (argument === "--help") return { help: true };
    if (argument === "--repo") options.repository = take();
    else if (argument === "--pr") options.pullNumber = parseInteger(take(), "--pr");
    else if (argument === "--head") options.headSha = take();
    else if (argument === "--base") options.baseSha = take();
    else if (argument === "--model") options.model = take();
    else if (argument === "--routing-context") options.routingContextPath = take();
    else if (argument === "--reasoning-effort") options.reasoningEffort = take();
    else if (argument === "--max-diff-chars") options.maxDiffChars = parseInteger(take(), "--max-diff-chars");
    else if (argument === "--max-output-tokens") options.maxOutputTokens = parseInteger(take(), "--max-output-tokens");
    else if (argument === "--max-request-bytes") options.maxRequestBytes = parseInteger(take(), "--max-request-bytes");
    else if (argument === "--provider-retries") options.providerRetries = parseNonNegativeInteger(take(), "--provider-retries");
    else if (argument === "--max-cost-usd") options.maxCostUsd = parsePositiveNumber(take(), "--max-cost-usd");
    else if (argument === "--output") options.output = take();
    else if (argument === "--state-dir") options.stateDirectory = take();
    else if (argument === "--reserve-only") options.reserveOnly = true;
    else if (argument === "--reservation-id") options.reservationId = take();
    else if (argument === "--resume-reservation") options.resumeReservationId = take();
    else if (argument === "--acknowledge-external-transfer") options.acknowledgeExternalTransfer = true;
    else if (argument === "--mock" || argument === "--live") {
      const mode = argument.slice(2);
      if (selectedMode && selectedMode !== mode) throw new Error("choose exactly one of --mock or --live");
      selectedMode = mode;
      options.mode = mode;
    } else throw new Error(`unknown argument: ${argument}`);
  }
  validateRepository(options.repository);
  if (!options.pullNumber) throw new Error("--pr is required");
  validateHeadSha(options.headSha);
  if (options.baseSha !== undefined) validateHeadSha(options.baseSha);
  validateModel(options.model);
  if (options.reasoningEffort !== undefined && !["low", "high"].includes(options.reasoningEffort)) throw new Error("--reasoning-effort must be low or high");
  if (options.reservationId !== undefined) validateReservationId(options.reservationId);
  if (options.resumeReservationId !== undefined) validateReservationId(options.resumeReservationId);
  if (options.maxOutputTokens > 16_000) throw new Error("--max-output-tokens must not exceed 16000");
  if (options.maxRequestBytes > 2_000_000) throw new Error("--max-request-bytes must not exceed 2000000");
  if (options.providerRetries !== 0) throw new Error("--provider-retries must be 0");
  if (options.maxCostUsd !== null && options.maxCostUsd > 1) throw new Error("--max-cost-usd must not exceed 1");
  if (options.mode === "live" && options.maxCostUsd === null) throw new Error("--max-cost-usd is required with --live");
  if (options.mode === "mock" && options.acknowledgeExternalTransfer) throw new Error("external-transfer acknowledgement is only valid with --live");
  if (options.mode === "mock" && (options.reserveOnly || options.reservationId !== undefined || options.resumeReservationId !== undefined)) {
    throw new Error("provider reservations are only valid with --live");
  }
  if (options.mode === "live" && options.baseSha === undefined) throw new Error("--base is required with --live");
  if (options.mode === "live" && options.reserveOnly !== (options.reservationId !== undefined)) {
    throw new Error("--reserve-only and --reservation-id must be used together");
  }
  if (options.mode === "live" && options.reserveOnly && options.resumeReservationId !== undefined) {
    throw new Error("choose exactly one of --reserve-only or --resume-reservation");
  }
  if (options.mode === "live" && !options.reserveOnly && options.resumeReservationId === undefined) {
    throw new Error("live mode requires --reserve-only or --resume-reservation");
  }
  return options;
}

function githubHeaders(token, accept = "application/vnd.github+json") {
  const headers = {
    Accept: accept,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "mile-commons-deepseek-review-v2",
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function githubRequest(url, { token, accept, responseType = "json" } = {}) {
  let response;
  try {
    response = await fetch(url, { headers: githubHeaders(token, accept), signal: AbortSignal.timeout(30_000) });
  } catch (error) {
    throw Object.assign(new Error(`GitHub request failed for ${new URL(url).pathname}`), { code: "GITHUB_NETWORK_ERROR", cause: error });
  }
  if (!response.ok) {
    throw Object.assign(new Error(`GitHub API returned HTTP ${response.status} for ${new URL(url).pathname}`), { code: `GITHUB_HTTP_${response.status}` });
  }
  if (responseType === "text") return response.text();
  try {
    return await response.json();
  } catch {
    throw Object.assign(new Error(`GitHub returned invalid JSON for ${new URL(url).pathname}`), { code: "GITHUB_INVALID_JSON" });
  }
}

export function createGitHubClient({ token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN } = {}) {
  return {
    async getPull(repository, pullNumber) {
      return githubRequest(`https://api.github.com/repos/${repository}/pulls/${pullNumber}`, { token });
    },
    async getComparison(repository, baseSha, headSha) {
      validateHeadSha(baseSha);
      validateHeadSha(headSha);
      const url = `https://api.github.com/repos/${repository}/compare/${baseSha}...${headSha}`;
      const [metadata, diff] = await Promise.all([
        githubRequest(url, { token }),
        githubRequest(url, { token, accept: "application/vnd.github.diff", responseType: "text" }),
      ]);
      if (!Array.isArray(metadata?.files) || !Array.isArray(metadata?.commits)) {
        throw Object.assign(new Error("GitHub comparison omitted its file or commit inventory"), { code: "GITHUB_COMPARE_INCOMPLETE" });
      }
      if (metadata.files.length >= 300) {
        throw Object.assign(new Error("GitHub comparison reached the ambiguous 300-file response limit"), { code: "GITHUB_COMPARE_FILE_LIMIT" });
      }
      if (!Number.isInteger(metadata.total_commits) || metadata.total_commits < 1 || metadata.total_commits !== metadata.commits.length) {
        throw Object.assign(new Error("GitHub comparison commit inventory is empty or truncated"), { code: "GITHUB_COMPARE_COMMIT_LIMIT" });
      }
      const resolvedHead = metadata.commits.at(-1)?.sha;
      return {
        complete: true,
        baseSha: metadata.base_commit?.sha,
        headSha: resolvedHead,
        mergeBaseSha: metadata.merge_base_commit?.sha,
        status: metadata.status,
        totalCommits: metadata.total_commits,
        files: metadata.files.map(({ filename, status, additions, deletions, changes }) => ({ filename, status, additions, deletions, changes })),
        diff,
      };
    },
  };
}

async function writeReport(output, report) {
  const destination = path.resolve(output);
  await mkdir(path.dirname(destination), { recursive: true });
  await writeFile(destination, `${JSON.stringify(report, null, 2)}\n`, { mode: 0o600 });
  return destination;
}

export async function main(argv) {
  let options;
  try {
    options = parseArgs(argv);
  } catch (error) {
    console.error(`deepseek-review: ${error.message}\n\n${USAGE}`);
    return 2;
  }
  if (options.help) {
    console.log(USAGE);
    return 0;
  }
  const reviewOptions = {
    repository: options.repository,
    routingContext: options.routingContextPath ? JSON.parse(await readFile(path.resolve(options.routingContextPath), "utf8")) : undefined,
    reasoningEffort: options.reasoningEffort,
    pullNumber: options.pullNumber,
    headSha: options.headSha,
    baseSha: options.baseSha,
    model: options.model,
    mode: options.mode,
    acknowledgeExternalTransfer: options.acknowledgeExternalTransfer,
    github: createGitHubClient(),
    apiKey: options.mode === "live" ? process.env.DEEPSEEK_API_KEY : undefined,
    maxDiffChars: options.maxDiffChars,
    maxOutputTokens: options.maxOutputTokens,
    maxRequestBytes: options.maxRequestBytes,
    providerRetries: options.providerRetries,
    maxCostUsd: options.maxCostUsd,
    reserveOnly: options.reserveOnly,
    reservationId: options.reservationId,
    resumeReservationId: options.resumeReservationId,
  };
  try {
    const { report, receiptPath } = await runReviewWithState({
      stateDirectory: path.resolve(options.stateDirectory),
      reviewOptions,
    });
    const outputPath = await writeReport(options.output, report);
    console.log(`deepseek-review: ${report.request_status}; ${report.review_status}`);
    console.log(`evidence: ${outputPath}`);
    console.log(`idempotency receipt: ${receiptPath}`);
    console.log(`exact head: ${report.exact_head_sha}`);
    console.log(`files covered: ${report.coverage.file_count}; blockers: ${report.blocker_count}; advisory: ${report.advisory_count}`);
    for (const error of report.errors) {
      console.error(`deepseek-review: ${error.code}: ${redactSecrets(error.message).text}`);
    }
    if (report.mode === "mock") console.log("MOCK ONLY: no DeepSeek API request was sent and this is not review approval.");
    const successfulMock = report.mode === "mock" && report.request_status === "MOCK_ONLY" && report.errors.length === 0
      && report.coverage.complete === true && report.coverage.file_count > 0
      && report.coverage.file_count === report.coverage.files.length && report.coverage.original_characters > 0;
    const successfulReservation = report.mode === "live"
      && report.request_status === "RESERVED"
      && report.provider_attempt_state === "REQUEST_MAY_HAVE_BEEN_SENT"
      && report.errors.length === 0;
    return successfulMock || successfulReservation || report.review_status === "REVIEW_COMPLETE" ? 0 : 1;
  } catch (error) {
    if (error.code === "DUPLICATE_INVOCATION" && error.receipt) {
      const outputPath = await writeReport(options.output, error.receipt);
      console.error(`deepseek-review: ${error.message}`);
      console.error(`existing evidence copied to: ${outputPath}`);
      return 3;
    }
    console.error(`deepseek-review: ${error.code ?? "ERROR"}: ${error.message}`);
    return 1;
  }
}

// This file is an entry point. Tests import only the side-effect-free core and
// exercise parseArgs by spawning the CLI when necessary.
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  process.exitCode = await main(process.argv.slice(2));
}
