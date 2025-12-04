import { create } from "zustand";
import { TestCase, RunStats } from "./types";
import { api } from "./api";

interface TrainingStore {
  // State
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

  // Actions
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

export const useTrainingStore = create<TrainingStore>((set, get) => ({
  // Initial state
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

  // Simple setters
  setIntent: (intent) => set({ intent }),
  setSystemPrompt: (systemPrompt) => set({ systemPrompt }),
  setSelectedModel: (selectedModel) => set({ selectedModel }),
  setGenerateCount: (generateCount) => set({ generateCount }),
  setActiveTab: (activeTab) => set({ activeTab }),
  clearError: () => set({ error: null }),

  // Test case mutations
  updateTestCase: (id, updates) =>
    set((state) => ({
      testCases: state.testCases.map((tc) =>
        tc.id === id ? { ...tc, ...updates } : tc
      ),
    })),

  deleteTestCase: (id) =>
    set((state) => ({
      testCases: state.testCases.filter((tc) => tc.id !== id),
    })),

  addTestCase: (testCase) =>
    set((state) => ({
      testCases: [...state.testCases, testCase],
    })),

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
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Split failed",
        isSplitting: false,
      });
    }
  },
}));
