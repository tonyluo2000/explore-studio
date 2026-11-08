#!/usr/bin/env node
import { budgetReport, recordOutcome } from './deepseek-budget.mjs';

export async function main(argv) {
  if (argv.length === 0 || argv[0] === 'report' && argv.length === 1) {
    console.log(JSON.stringify(await budgetReport(), null, 2));
    return;
  }
  if (argv[0] === 'outcome' && argv.length === 5 && ['accepted', 'rejected'].includes(argv[2]) && ['rework', 'no-rework'].includes(argv[3])) {
    await recordOutcome({ requestId: argv[1], accepted: argv[2] === 'accepted', rework: argv[3] === 'rework', findingCounts: JSON.parse(argv[4]) });
    console.log('Outcome appended. Release authority: NONE.');
    return;
  }
  throw new Error('usage: deepseek-usage.mjs report | outcome REQUEST_SHA256 accepted|rejected rework|no-rework \'{"P0":0,"P1":0,"P2":0,"P3":0}\'');
}
if (process.argv[1]?.endsWith('/deepseek-usage.mjs')) main(process.argv.slice(2)).catch(error => { console.error(error.code ?? error.message); process.exitCode = 1; });
