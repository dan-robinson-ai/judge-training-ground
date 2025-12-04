import { Dataset, DatasetListItem } from "../types";

export interface DatasetStorageProvider {
  getAllDatasets(): Promise<DatasetListItem[]>;
  getDataset(id: string): Promise<Dataset | null>;
  saveDataset(dataset: Dataset): Promise<void>;
  deleteDataset(id: string): Promise<void>;
}
