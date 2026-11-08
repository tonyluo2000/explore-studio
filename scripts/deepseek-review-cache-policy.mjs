#!/usr/bin/env node
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { isRecoverablePreflightReceipt } from "./deepseek-review-core.mjs";

export function shouldPersistReviewState({ mode, receipts }) {
  if (mode === "mock") return true;
  if (mode !== "live") throw new Error("mode must be mock or live");
  if (!Array.isArray(receipts)) return true;
  if (receipts.length === 0) return false;
  if (receipts.length !== 1) return true;
  return !isRecoverablePreflightReceipt(receipts[0]);
}

async function readReceipts(stateDirectory) {
  let entries;
  try {
    entries = await readdir(stateDirectory, { withFileTypes: true });
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
  const receiptNames = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
    .map((entry) => entry.name)
    .sort();
  return Promise.all(receiptNames.map(async (name) => JSON.parse(
    await readFile(path.join(stateDirectory, name), "utf8"),
  )));
}

export async function main(argv) {
  const [stateDirectory, mode] = argv;
  if (!stateDirectory || !mode) throw new Error("usage: deepseek-review-cache-policy STATE_DIRECTORY MODE");
  const receipts = await readReceipts(path.resolve(stateDirectory));
  console.log(`persist=${shouldPersistReviewState({ mode, receipts })}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  await main(process.argv.slice(2));
}
