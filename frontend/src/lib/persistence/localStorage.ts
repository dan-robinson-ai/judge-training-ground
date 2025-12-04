import { Dataset, DatasetListItem } from "../types";
import { DatasetStorageProvider } from "./types";
import { needsMigration, migrateJudgesToDatasets, NEW_STORAGE_KEYS } from "./migration";

const { INDEX_KEY, DATASET_PREFIX } = NEW_STORAGE_KEYS;

export class LocalStorageProvider implements DatasetStorageProvider {
  private ensureMigrated() {
    if (needsMigration()) {
      migrateJudgesToDatasets();
    }
  }

  async getAllDatasets(): Promise<DatasetListItem[]> {
    if (typeof window === "undefined") return [];
    this.ensureMigrated();
    const index = localStorage.getItem(INDEX_KEY);
    return index ? JSON.parse(index) : [];
  }

  async getDataset(id: string): Promise<Dataset | null> {
    if (typeof window === "undefined") return null;
    this.ensureMigrated();
    const data = localStorage.getItem(`${DATASET_PREFIX}${id}`);
    return data ? JSON.parse(data) : null;
  }

  async saveDataset(dataset: Dataset): Promise<void> {
    if (typeof window === "undefined") return;

    const updatedDataset = {
      ...dataset,
      updatedAt: new Date().toISOString(),
    };

    localStorage.setItem(
      `${DATASET_PREFIX}${dataset.id}`,
      JSON.stringify(updatedDataset)
    );

    // Update index
    const index = await this.getAllDatasets();
    const bestAccuracy =
      dataset.runs.length > 0
        ? Math.max(...dataset.runs.map((r) => r.stats.accuracy))
        : null;

    const listItem: DatasetListItem = {
      id: dataset.id,
      name: dataset.name,
      createdAt: dataset.createdAt,
      updatedAt: updatedDataset.updatedAt,
      testCaseCount: dataset.testCases.length,
      promptVersionCount: dataset.promptVersions.length,
      bestAccuracy,
    };

    const existingIdx = index.findIndex((d) => d.id === dataset.id);
    if (existingIdx >= 0) {
      index[existingIdx] = listItem;
    } else {
      index.push(listItem);
    }
    localStorage.setItem(INDEX_KEY, JSON.stringify(index));
  }

  async deleteDataset(id: string): Promise<void> {
    if (typeof window === "undefined") return;
    localStorage.removeItem(`${DATASET_PREFIX}${id}`);
    const index = await this.getAllDatasets();
    localStorage.setItem(
      INDEX_KEY,
      JSON.stringify(index.filter((d) => d.id !== id))
    );
  }
}
