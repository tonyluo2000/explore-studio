import { readFileSync } from 'node:fs';

const configuration = JSON.parse(readFileSync(new URL('../config/ai-model-routing.json', import.meta.url), 'utf8'));
const families = new Set(['deepseek', 'openai', 'claude']);

export function resolveRoute({ repository, taskType, implementerFamily, overrides = {} }) {
  if (!Object.hasOwn(configuration.projects, repository)) throw new Error('UNAPPROVED_REPOSITORY');
  if (taskType === 'release') return { authority: configuration.releaseAuthority, automatic: false, model: null };
  if (!Object.hasOwn(configuration.tasks, taskType)) throw new Error('UNKNOWN_TASK_TYPE');
  const project = configuration.projects[repository];
  const route = { ...configuration.tasks[taskType], ...project[taskType], ...overrides };
  if (!['deepseek','openai','anthropic'].includes(route.provider)) throw new Error('UNKNOWN_PROVIDER');
  if (!families.has(route.family) || !['low','medium','high'].includes(route.reasoningEffort)) throw new Error('INVALID_ROUTE');
  if (route.provider === 'deepseek' && (!['deepseek-flash','deepseek-v4-pro'].includes(route.model) || route.family !== 'deepseek')) throw new Error('INVALID_DEEPSEEK_ROUTE');
  if (route.provider === 'openai' && route.family !== 'openai' || route.provider === 'anthropic' && route.family !== 'claude') throw new Error('PROVIDER_FAMILY_MISMATCH');
  if (['review', 'security'].includes(taskType)) {
    if (!families.has(implementerFamily)) throw new Error('IMPLEMENTER_FAMILY_REQUIRED');
    if (route.family === implementerFamily) throw new Error('INDEPENDENT_MODEL_REQUIRED');
  }
  return { ...route, automaticFallback: false, repository, taskType, approvalAuthority: 'NONE' };
}
