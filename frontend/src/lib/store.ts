import { create } from "zustand";
import { TestCase, RunStats, Judge, JudgeListItem } from "./types";
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

  // Judge collection state
  judges: JudgeListItem[];
  activeJudgeId: string | null;
  isLoadingJudges: boolean;

  // Active judge state
  intent: string;
  systemPrompt: string;
  testCases: TestCase[];
  runStats: RunStats | null;
  selectedModel: string;
  generateCount: number;
  hasGenerated: boolean;
  isGenerating: boolean;
  isRunning: boolean;
  isOptimizing: boolean;
  isSplitting: boolean;
  isSplit: boolean;
  error: string | null;
  activeTab: "dataset" | "results";

  // UI Actions
  toggleSidebar: () => void;

  // Judge management actions
  loadJudges: () => Promise<void>;
  selectJudge: (id: string) => Promise<void>;
  createJudge: (name?: string) => Promise<string>;
  deleteJudge: (id: string) => Promise<void>;
  renameJudge: (id: string, newName: string) => Promise<void>;

  // State setters
  setIntent: (intent: string) => void;
  setSystemPrompt: (prompt: string) => void;
  setSelectedModel: (model: string) => void;
  setGenerateCount: (count: number) => void;
  setActiveTab: (tab: "dataset" | "results") => void;
  clearError: () => void;

  // Test case mutations
  updateTestCase: (id: string, updates: Partial<TestCase>) => void;
  deleteTestCase: (id: string) => void;
  addTestCase: (testCase: TestCase) => void;

  // Async actions
  generateTestCases: () => Promise<void>;
  runEvaluation: () => Promise<void>;
  optimizePrompt: () => Promise<void>;
  splitDataset: () => Promise<void>;
}

// Helper to build a Judge object from current state
function buildJudgeFromState(state: TrainingStore, id: string, name: string, createdAt: string): Judge {
  return {
    id,
    name,
    createdAt,
    updatedAt: new Date().toISOString(),
    intent: state.intent,
    systemPrompt: state.systemPrompt,
    testCases: state.testCases,
    runStats: state.runStats,
    selectedModel: state.selectedModel,
    generateCount: state.generateCount,
    hasGenerated: state.hasGenerated,
    isSplit: state.isSplit,
  };
}

// Create debounced persist function
const debouncedPersist = debounce(async (get: () => TrainingStore) => {
  const state = get();
  if (!state.activeJudgeId) return;

  const currentJudge = state.judges.find((j) => j.id === state.activeJudgeId);
  if (!currentJudge) return;

  const judge = buildJudgeFromState(
    state,
    state.activeJudgeId,
    currentJudge.name,
    currentJudge.createdAt
  );

  await storage.saveJudge(judge);

  // Update judges list with new metadata
  const updatedJudges = state.judges.map((j) =>
    j.id === state.activeJudgeId
      ? {
          ...j,
          updatedAt: judge.updatedAt,
          testCaseCount: judge.testCases.length,
          accuracy: judge.runStats?.accuracy ?? null,
        }
      : j
  );

  // Only update if we're still on the same judge
  if (get().activeJudgeId === state.activeJudgeId) {
    useTrainingStore.setState({ judges: updatedJudges });
  }
}, 500);

export const useTrainingStore = create<TrainingStore>((set, get) => ({
  // Initial state
  sidebarCollapsed: false,
  judges: [],
  activeJudgeId: null,
  isLoadingJudges: false,

  intent: "",
  systemPrompt: "",
  testCases: [],
  runStats: null,
  selectedModel: "gpt-4o",
  generateCount: 50,
  hasGenerated: false,
  isGenerating: false,
  isRunning: false,
  isOptimizing: false,
  isSplitting: false,
  isSplit: false,
  error: null,
  activeTab: "dataset",

  // UI Actions
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  // Judge management actions
  loadJudges: async () => {
    set({ isLoadingJudges: true });
    try {
      const judges = await storage.getAllJudges();

      if (judges.length > 0) {
        // Sort by updatedAt descending and select most recent
        const sorted = [...judges].sort(
          (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        );
        set({ judges: sorted, isLoadingJudges: false });

        // Auto-select most recently updated judge
        await get().selectJudge(sorted[0].id);
      } else {
        set({ judges: [], isLoadingJudges: false });
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to load judges",
        isLoadingJudges: false,
      });
    }
  },

  selectJudge: async (id: string) => {
    const state = get();

    // Save current judge first if there is one
    if (state.activeJudgeId) {
      const currentJudge = state.judges.find((j) => j.id === state.activeJudgeId);
      if (currentJudge) {
        const judge = buildJudgeFromState(
          state,
          state.activeJudgeId,
          currentJudge.name,
          currentJudge.createdAt
        );
        await storage.saveJudge(judge);
      }
    }

    // Load new judge
    const judge = await storage.getJudge(id);
    if (judge) {
      set({
        activeJudgeId: id,
        intent: judge.intent,
        systemPrompt: judge.systemPrompt,
        testCases: judge.testCases,
        runStats: judge.runStats,
        selectedModel: judge.selectedModel,
        generateCount: judge.generateCount,
        hasGenerated: judge.hasGenerated,
        isSplit: judge.isSplit,
        error: null,
        activeTab: "dataset",
      });
    }
  },

  createJudge: async (name?: string) => {
    const state = get();
    const judgeName = name || `Judge ${state.judges.length + 1}`;
    const now = new Date().toISOString();
    const id = crypto.randomUUID();

    const newJudge: Judge = {
      id,
      name: judgeName,
      createdAt: now,
      updatedAt: now,
      intent: "",
      systemPrompt: "",
      testCases: [],
      runStats: null,
      selectedModel: "gpt-4o",
      generateCount: 50,
      hasGenerated: false,
      isSplit: false,
    };

    await storage.saveJudge(newJudge);

    const listItem: JudgeListItem = {
      id,
      name: judgeName,
      createdAt: now,
      updatedAt: now,
      testCaseCount: 0,
      accuracy: null,
    };

    set((state) => ({
      judges: [listItem, ...state.judges],
    }));

    // Select the new judge
    await get().selectJudge(id);

    return id;
  },

  deleteJudge: async (id: string) => {
    await storage.deleteJudge(id);

    const state = get();
    const updatedJudges = state.judges.filter((j) => j.id !== id);

    set({ judges: updatedJudges });

    // If we deleted the active judge, select another one
    if (state.activeJudgeId === id) {
      if (updatedJudges.length > 0) {
        await get().selectJudge(updatedJudges[0].id);
      } else {
        // No judges left, reset state
        set({
          activeJudgeId: null,
          intent: "",
          systemPrompt: "",
          testCases: [],
          runStats: null,
          selectedModel: "gpt-4o",
          generateCount: 50,
          hasGenerated: false,
          isSplit: false,
        });
      }
    }
  },

  renameJudge: async (id: string, newName: string) => {
    const judge = await storage.getJudge(id);
    if (judge) {
      judge.name = newName;
      await storage.saveJudge(judge);

      set((state) => ({
        judges: state.judges.map((j) =>
          j.id === id ? { ...j, name: newName } : j
        ),
      }));
    }
  },

  // Simple setters (with auto-persist)
  setIntent: (intent) => {
    set({ intent });
    debouncedPersist(get);
  },
  setSystemPrompt: (systemPrompt) => {
    set({ systemPrompt });
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
  setActiveTab: (activeTab) => set({ activeTab }),
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
      const response = await api.generateTestCases(intent, generateCount, selectedModel);
      set({
        testCases: response.test_cases,
        systemPrompt: response.system_prompt,
        hasGenerated: true,
        isGenerating: false,
        isSplit: false,
        runStats: null,
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
    const { systemPrompt, testCases, selectedModel } = get();
    if (testCases.length === 0) {
      set({ error: "No test cases to evaluate" });
      return;
    }

    set({ isRunning: true, error: null });
    try {
      const runStats = await api.runEvaluation(
        systemPrompt,
        testCases,
        selectedModel
      );
      set({ runStats, isRunning: false, activeTab: "results" });
      debouncedPersist(get);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Evaluation failed",
        isRunning: false,
      });
    }
  },

  optimizePrompt: async () => {
    const { systemPrompt, testCases, runStats } = get();
    if (!runStats) {
      set({ error: "Run an evaluation first" });
      return;
    }

    set({ isOptimizing: true, error: null });
    try {
      const result = await api.optimizePrompt(
        systemPrompt,
        testCases,
        runStats.results
      );
      set({
        systemPrompt: result.optimized_prompt,
        isOptimizing: false,
      });
      debouncedPersist(get);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Optimization failed",
        isOptimizing: false,
      });
    }
  },

  splitDataset: async () => {
    const { testCases, isSplit } = get();
    if (testCases.length === 0) {
      set({ error: "No test cases to split" });
      return;
    }
    if (isSplit) {
      set({ error: "Dataset is already split" });
      return;
    }

    set({ isSplitting: true, error: null });
    try {
      const response = await api.splitDataset(testCases);
      set({
        testCases: [...response.train_cases, ...response.test_cases],
        isSplit: true,
        isSplitting: false,
      });
      debouncedPersist(get);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Split failed",
        isSplitting: false,
      });
    }
  },
}));
