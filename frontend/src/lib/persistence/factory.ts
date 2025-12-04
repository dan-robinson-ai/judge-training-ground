import { JudgeStorageProvider } from "./types";
import { LocalStorageProvider } from "./localStorage";

type StorageType = "localStorage" | "backend";

export function createStorageProvider(
  type: StorageType = "localStorage"
): JudgeStorageProvider {
  switch (type) {
    case "localStorage":
      return new LocalStorageProvider();
    case "backend":
      // Future: return new BackendApiProvider(apiClient);
      throw new Error("Backend storage not yet implemented");
    default:
      return new LocalStorageProvider();
  }
}

// Singleton instance for app use
export const storage = createStorageProvider("localStorage");
