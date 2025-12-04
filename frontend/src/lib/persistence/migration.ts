import { Judge, Dataset, PromptVersion, Run, DatasetListItem } from "../types";

const MIGRATION_VERSION_KEY = "judge-training-migration-version";
const CURRENT_MIGRATION_VERSION = 1;
const OLD_INDEX_KEY = "judge-training-index";
const OLD_JUDGE_PREFIX = "judge-training-judges-";
const NEW_INDEX_KEY = "dataset-training-index";
const NEW_DATASET_PREFIX = "dataset-training-datasets-";

export function needsMigration(): boolean {
  if (typeof window === "undefined") return false;
  const version = localStorage.getItem(MIGRATION_VERSION_KEY);
  return version !== String(CURRENT_MIGRATION_VERSION);
}

export function migrateJudgesToDatasets(): void {
  if (typeof window === "undefined") return;
  if (!needsMigration()) return;

  const oldIndex = localStorage.getItem(OLD_INDEX_KEY);
  if (!oldIndex) {
    // No old data, just mark as migrated
    localStorage.setItem(MIGRATION_VERSION_KEY, String(CURRENT_MIGRATION_VERSION));
    return;
  }

  const judgeListItems: { id: string }[] = JSON.parse(oldIndex);
  const datasetListItems: DatasetListItem[] = [];

  for (const item of judgeListItems) {
    const judgeData = localStorage.getItem(`${OLD_JUDGE_PREFIX}${item.id}`);
    if (!judgeData) continue;

    const judge: Judge = JSON.parse(judgeData);

    // Create initial prompt version if judge has a system prompt
    const promptVersions: PromptVersion[] = [];
    let activePromptVersionId: string | null = null;

    if (judge.systemPrompt) {
      const promptVersion: PromptVersion = {
        id: crypto.randomUUID(),
        version: 1,
        systemPrompt: judge.systemPrompt,
        source: judge.hasGenerated ? "generated" : "manual",
        createdAt: judge.createdAt,
        parentVersionId: null,
      };
      promptVersions.push(promptVersion);
      activePromptVersionId = promptVersion.id;
    }

    // Create runs from existing runStats
    const runs: Run[] = [];
    if (judge.runStats && activePromptVersionId) {
      runs.push({
        id: crypto.randomUUID(),
        promptVersionId: activePromptVersionId,
        modelName: judge.selectedModel,
        createdAt: judge.updatedAt,
        stats: judge.runStats,
      });
    }

    const dataset: Dataset = {
      id: judge.id,
      name: judge.name,
      createdAt: judge.createdAt,
      updatedAt: judge.updatedAt,
      intent: judge.intent,
      testCases: judge.testCases,
      promptVersions,
      runs,
      activePromptVersionId,
      generateCount: judge.generateCount,
      hasGenerated: judge.hasGenerated,
      isSplit: judge.isSplit,
    };

    // Save new dataset
    localStorage.setItem(
      `${NEW_DATASET_PREFIX}${dataset.id}`,
      JSON.stringify(dataset)
    );

    // Build list item
    datasetListItems.push({
      id: dataset.id,
      name: dataset.name,
      createdAt: dataset.createdAt,
      updatedAt: dataset.updatedAt,
      testCaseCount: dataset.testCases.length,
      promptVersionCount: promptVersions.length,
      bestAccuracy: runs.length > 0 ? runs[0].stats.accuracy : null,
    });

    // Remove old judge data
    localStorage.removeItem(`${OLD_JUDGE_PREFIX}${item.id}`);
  }

  // Save new index and remove old
  localStorage.setItem(NEW_INDEX_KEY, JSON.stringify(datasetListItems));
  localStorage.removeItem(OLD_INDEX_KEY);
  localStorage.setItem(MIGRATION_VERSION_KEY, String(CURRENT_MIGRATION_VERSION));
}

export const NEW_STORAGE_KEYS = {
  INDEX_KEY: NEW_INDEX_KEY,
  DATASET_PREFIX: NEW_DATASET_PREFIX,
};
