import { create } from "zustand";
import {
  TestCase,
  RunStats,
  Dataset,
  DatasetListItem,
  PromptVersion,
  Run,
  OptimizerType,
} from "./types";
import { api } from "./api";
import { storage } from "./persistence";

// Debounce helper
function debounce<Args extends unknown[]>(
  fn: (...args: Args) => void,
  ms: number
): (...args: Args) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  return (...args: Args) => {
    if (timeoutId) clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), ms);
  };
}

interface TrainingStore {
  // App-level UI state
  sidebarCollapsed: boolean;

  // Dataset collection state
  datasets: DatasetListItem[];
  activeDatasetId: string | null;
  isLoadingDatasets: boolean;

  // Active dataset state (flattened for convenience)
  intent: string;
  testCases: TestCase[];
  promptVersions: PromptVersion[];
  runs: Run[];
  activePromptVersionId: string | null;

  // Current editing state
  currentSystemPrompt: string;
  selectedModel: string;
  generateCount: number;
  optimizerType: OptimizerType;

  // Flags
  hasGenerated: boolean;
  isGenerating: boolean;
  isRunning: boolean;
  isOptimizing: boolean;
  isSplit: boolean;
  error: string | null;

  // UI state
  activeTab: "dataset" | "versions" | "history";

  // UI Actions
  toggleSidebar: () => void;
  setActiveTab: (tab: "dataset" | "versions" | "history") => void;

  // Dataset management
  loadDatasets: () => Promise<void>;
  selectDataset: (id: string) => Promise<void>;
  createDataset: (name?: string) => Promise<string>;
  deleteDataset: (id: string) => Promise<void>;
  renameDataset: (id: string, newName: string) => Promise<void>;

  // Prompt version management
  selectPromptVersion: (versionId: string) => void;
  savePromptVersion: (notes?: string) => Promise<void>;

  // State setters
  setIntent: (intent: string) => void;
  setCurrentSystemPrompt: (prompt: string) => void;
  setSelectedModel: (model: string) => void;
  setGenerateCount: (count: number) => void;
  setOptimizerType: (optimizerType: OptimizerType) => void;
  clearError: () => void;

  // Test case mutations
  updateTestCase: (id: string, updates: Partial<TestCase>) => void;
  deleteTestCase: (id: string) => void;
  addTestCase: (testCase: TestCase) => void;

  // Async actions
  generateTestCases: () => Promise<void>;
  runEvaluation: () => Promise<void>;
  optimizePrompt: () => Promise<void>;
}

// Helper to get next version number
function getNextVersionNumber(versions: PromptVersion[]): number {
  if (versions.length === 0) return 1;
  return Math.max(...versions.map((v) => v.version)) + 1;
}

// Helper to build a Dataset object from current state
function buildDatasetFromState(
  state: TrainingStore,
  id: string,
  name: string,
  createdAt: string
): Dataset {
  return {
    id,
    name,
    createdAt,
    updatedAt: new Date().toISOString(),
    intent: state.intent,
    testCases: state.testCases,
    promptVersions: state.promptVersions,
    runs: state.runs,
    activePromptVersionId: state.activePromptVersionId,
    generateCount: state.generateCount,
    hasGenerated: state.hasGenerated,
    isSplit: state.isSplit,
  };
}

// Create debounced persist function
const debouncedPersist = debounce(async (get: () => TrainingStore) => {
  const state = get();
  if (!state.activeDatasetId) return;

  const currentDataset = state.datasets.find(
    (d) => d.id === state.activeDatasetId
  );
  if (!currentDataset) return;

  const dataset = buildDatasetFromState(
    state,
    state.activeDatasetId,
    currentDataset.name,
    currentDataset.createdAt
  );

  await storage.saveDataset(dataset);

  // Update datasets list with new metadata
  const bestAccuracy =
    dataset.runs.length > 0
      ? Math.max(...dataset.runs.map((r) => r.stats.accuracy))
      : null;

  const updatedDatasets = state.datasets.map((d) =>
    d.id === state.activeDatasetId
      ? {
          ...d,
          updatedAt: dataset.updatedAt,
          testCaseCount: dataset.testCases.length,
          promptVersionCount: dataset.promptVersions.length,
          bestAccuracy,
        }
      : d
  );

  // Only update if we're still on the same dataset
  if (get().activeDatasetId === state.activeDatasetId) {
    useTrainingStore.setState({ datasets: updatedDatasets });
  }
}, 500);

export const useTrainingStore = create<TrainingStore>((set, get) => ({
  // Initial state
  sidebarCollapsed: false,
  datasets: [],
  activeDatasetId: null,
  isLoadingDatasets: false,

  intent: "",
  testCases: [],
  promptVersions: [],
  runs: [],
  activePromptVersionId: null,
  currentSystemPrompt: "",
  selectedModel: "gpt-4o",
  generateCount: 50,
  optimizerType: "bootstrap_fewshot" as OptimizerType,
  hasGenerated: false,
  isGenerating: false,
  isRunning: false,
  isOptimizing: false,
  isSplit: false,
  error: null,
  activeTab: "dataset",

  // UI Actions
  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setActiveTab: (activeTab) => set({ activeTab }),

  // Dataset management actions
  loadDatasets: async () => {
    set({ isLoadingDatasets: true });
    try {
      const datasets = await storage.getAllDatasets();

      if (datasets.length > 0) {
        // Sort by updatedAt descending and select most recent
        const sorted = [...datasets].sort(
          (a, b) =>
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        );
        set({ datasets: sorted, isLoadingDatasets: false });

        // Auto-select most recently updated dataset
        await get().selectDataset(sorted[0].id);
      } else {
        set({ datasets: [], isLoadingDatasets: false });
      }
    } catch (error) {
      set({
        error:
          error instanceof Error ? error.message : "Failed to load datasets",
        isLoadingDatasets: false,
      });
    }
  },

  selectDataset: async (id: string) => {
    const state = get();

    // Save current dataset first if there is one
    if (state.activeDatasetId) {
      const currentDataset = state.datasets.find(
        (d) => d.id === state.activeDatasetId
      );
      if (currentDataset) {
        const dataset = buildDatasetFromState(
          state,
          state.activeDatasetId,
          currentDataset.name,
          currentDataset.createdAt
        );
        await storage.saveDataset(dataset);
      }
    }

    // Load new dataset
    const dataset = await storage.getDataset(id);
    if (dataset) {
      // Find active prompt version
      const activeVersion = dataset.promptVersions.find(
        (v) => v.id === dataset.activePromptVersionId
      );

      set({
        activeDatasetId: id,
        intent: dataset.intent,
        testCases: dataset.testCases,
        promptVersions: dataset.promptVersions,
        runs: dataset.runs,
        activePromptVersionId: dataset.activePromptVersionId,
        currentSystemPrompt: activeVersion?.systemPrompt ?? "",
        generateCount: dataset.generateCount,
        hasGenerated: dataset.hasGenerated,
        isSplit: dataset.isSplit,
        error: null,
        activeTab: "dataset",
      });
    }
  },

  createDataset: async (name?: string) => {
    const state = get();
    const datasetName = name || `Dataset ${state.datasets.length + 1}`;
    const now = new Date().toISOString();
    const id = crypto.randomUUID();

    const newDataset: Dataset = {
      id,
      name: datasetName,
      createdAt: now,
      updatedAt: now,
      intent: "",
      testCases: [],
      promptVersions: [],
      runs: [],
      activePromptVersionId: null,
      generateCount: 50,
      hasGenerated: false,
      isSplit: false,
    };

    await storage.saveDataset(newDataset);

    const listItem: DatasetListItem = {
      id,
      name: datasetName,
      createdAt: now,
      updatedAt: now,
      testCaseCount: 0,
      promptVersionCount: 0,
      bestAccuracy: null,
    };

    set((state) => ({
      datasets: [listItem, ...state.datasets],
    }));

    // Select the new dataset
    await get().selectDataset(id);

    return id;
  },

  deleteDataset: async (id: string) => {
    await storage.deleteDataset(id);

    const state = get();
    const updatedDatasets = state.datasets.filter((d) => d.id !== id);

    set({ datasets: updatedDatasets });

    // If we deleted the active dataset, select another one
    if (state.activeDatasetId === id) {
      if (updatedDatasets.length > 0) {
        await get().selectDataset(updatedDatasets[0].id);
      } else {
        // No datasets left, reset state
        set({
          activeDatasetId: null,
          intent: "",
          testCases: [],
          promptVersions: [],
          runs: [],
          activePromptVersionId: null,
          currentSystemPrompt: "",
          generateCount: 50,
          hasGenerated: false,
          isSplit: false,
        });
      }
    }
  },

  renameDataset: async (id: string, newName: string) => {
    const dataset = await storage.getDataset(id);
    if (dataset) {
      dataset.name = newName;
      await storage.saveDataset(dataset);

      set((state) => ({
        datasets: state.datasets.map((d) =>
          d.id === id ? { ...d, name: newName } : d
        ),
      }));
    }
  },

  // Prompt version management
  selectPromptVersion: (versionId: string) => {
    const state = get();
    const version = state.promptVersions.find((v) => v.id === versionId);
    if (version) {
      set({
        activePromptVersionId: versionId,
        currentSystemPrompt: version.systemPrompt,
      });
      debouncedPersist(get);
    }
  },

  savePromptVersion: async (notes?: string) => {
    const state = get();
    if (!state.currentSystemPrompt.trim()) return;

    const newVersion: PromptVersion = {
      id: crypto.randomUUID(),
      version: getNextVersionNumber(state.promptVersions),
      systemPrompt: state.currentSystemPrompt,
      source: "manual",
      createdAt: new Date().toISOString(),
      parentVersionId: state.activePromptVersionId,
      notes,
    };

    set({
      promptVersions: [...state.promptVersions, newVersion],
      activePromptVersionId: newVersion.id,
    });
    debouncedPersist(get);
  },

  // Simple setters (with auto-persist)
  setIntent: (intent) => {
    set({ intent });
    debouncedPersist(get);
  },
  setCurrentSystemPrompt: (currentSystemPrompt) => {
    set({ currentSystemPrompt });
    debouncedPersist(get);
  },
  setSelectedModel: (selectedModel) => {
    set({ selectedModel });
    debouncedPersist(get);
  },
  setGenerateCount: (generateCount) => {
    set({ generateCount });
    debouncedPersist(get);
  },
  setOptimizerType: (optimizerType) => {
    set({ optimizerType });
  },
  clearError: () => set({ error: null }),

  // Test case mutations (with auto-persist)
  updateTestCase: (id, updates) => {
    set((state) => ({
      testCases: state.testCases.map((tc) =>
        tc.id === id ? { ...tc, ...updates } : tc
      ),
    }));
    debouncedPersist(get);
  },

  deleteTestCase: (id) => {
    set((state) => ({
      testCases: state.testCases.filter((tc) => tc.id !== id),
    }));
    debouncedPersist(get);
  },

  addTestCase: (testCase) => {
    set((state) => ({
      testCases: [...state.testCases, testCase],
    }));
    debouncedPersist(get);
  },

  // Async actions
  generateTestCases: async () => {
    const { intent, generateCount, selectedModel } = get();
    if (!intent.trim()) {
      set({ error: "Please enter an intent first" });
      return;
    }

    set({ isGenerating: true, error: null });
    try {
      const response = await api.generateTestCases(
        intent,
        generateCount,
        selectedModel
      );

      // Create new prompt version from generated prompt
      const state = get();
      const newVersion: PromptVersion = {
        id: crypto.randomUUID(),
        version: getNextVersionNumber(state.promptVersions),
        systemPrompt: response.system_prompt,
        source: "generated",
        createdAt: new Date().toISOString(),
        parentVersionId: null,
      };

      set({
        testCases: response.test_cases,
        promptVersions: [...state.promptVersions, newVersion],
        activePromptVersionId: newVersion.id,
        currentSystemPrompt: response.system_prompt,
        hasGenerated: true,
        isGenerating: false,
        isSplit: false,
        runs: [], // Clear runs when regenerating
      });
      debouncedPersist(get);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Generation failed",
        isGenerating: false,
      });
    }
  },

  runEvaluation: async () => {
    const state = get();
    const { currentSystemPrompt, testCases, selectedModel, activePromptVersionId } = state;

    if (testCases.length === 0) {
      set({ error: "No test cases to evaluate" });
      return;
    }

    if (!activePromptVersionId) {
      set({ error: "No prompt version selected" });
      return;
    }

    set({ isRunning: true, error: null });
    try {
      const runStats: RunStats = await api.runEvaluation(
        currentSystemPrompt,
        testCases,
        selectedModel
      );

      // Create new run entry
      const newRun: Run = {
        id: crypto.randomUUID(),
        promptVersionId: activePromptVersionId,
        modelName: selectedModel,
        createdAt: new Date().toISOString(),
        stats: runStats,
      };

      set({
        runs: [...state.runs, newRun],
        isRunning: false,
        activeTab: "history",
      });
      debouncedPersist(get);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Evaluation failed",
        isRunning: false,
      });
    }
  },

  optimizePrompt: async () => {
    const state = get();
    const {
      currentSystemPrompt,
      testCases,
      runs,
      activePromptVersionId,
      optimizerType,
      selectedModel,
    } = state;

    // Find the most recent run for current version
    const relevantRuns = runs.filter(
      (r) => r.promptVersionId === activePromptVersionId
    );
    if (relevantRuns.length === 0) {
      set({ error: "Run an evaluation first" });
      return;
    }

    const lastRun = relevantRuns[relevantRuns.length - 1];

    set({ isOptimizing: true, error: null });
    try {
      const result = await api.optimizePrompt(
        currentSystemPrompt,
        testCases,
        lastRun.stats.results,
        optimizerType,
        selectedModel
      );

      // Create new version from optimization
      const newVersion: PromptVersion = {
        id: crypto.randomUUID(),
        version: getNextVersionNumber(state.promptVersions),
        systemPrompt: result.optimized_prompt,
        source: "optimized",
        createdAt: new Date().toISOString(),
        parentVersionId: activePromptVersionId,
        notes: result.modification_notes,
        optimizerType,
      };

      set({
        promptVersions: [...state.promptVersions, newVersion],
        activePromptVersionId: newVersion.id,
        currentSystemPrompt: result.optimized_prompt,
        testCases: [...result.train_cases, ...result.test_cases],
        isSplit: true,
        isOptimizing: false,
        activeTab: "versions",
      });
      debouncedPersist(get);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Optimization failed",
        isOptimizing: false,
      });
    }
  },
}));
