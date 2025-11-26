import { create } from "zustand";
import { TestCase, EvaluationResult, RunStats } from "./types";
import { api } from "./api";

interface TrainingStore {
  // State
  intent: string;
  systemPrompt: string;
  testCases: TestCase[];
  runStats: RunStats | null;
  selectedModel: string;
  isGenerating: boolean;
  isRunning: boolean;
  isOptimizing: boolean;
  error: string | null;
  activeTab: "dataset" | "results";

  // Actions
  setIntent: (intent: string) => void;
  setSystemPrompt: (prompt: string) => void;
  setSelectedModel: (model: string) => void;
  setActiveTab: (tab: "dataset" | "results") => void;
  clearError: () => void;

  // Test case mutations
  updateTestCase: (id: string, updates: Partial<TestCase>) => void;
  deleteTestCase: (id: string) => void;
  addTestCase: (testCase: TestCase) => void;

  // Async actions
  generateTestCases: (count?: number) => Promise<void>;
  runEvaluation: () => Promise<void>;
  optimizePrompt: () => Promise<void>;
}

const DEFAULT_SYSTEM_PROMPT = `You are a content moderation judge. Your task is to evaluate user inputs and determine if they should PASS or FAIL based on the following criteria:

- PASS: The content is appropriate, helpful, and does not violate any guidelines.
- FAIL: The content is inappropriate, harmful, or violates guidelines.

Be thorough in your analysis and consider edge cases carefully.`;

export const useTrainingStore = create<TrainingStore>((set, get) => ({
  // Initial state
  intent: "",
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
  testCases: [],
  runStats: null,
  selectedModel: "gpt-4o",
  isGenerating: false,
  isRunning: false,
  isOptimizing: false,
  error: null,
  activeTab: "dataset",

  // Simple setters
  setIntent: (intent) => set({ intent }),
  setSystemPrompt: (systemPrompt) => set({ systemPrompt }),
  setSelectedModel: (selectedModel) => set({ selectedModel }),
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
  generateTestCases: async (count = 10) => {
    const { intent } = get();
    if (!intent.trim()) {
      set({ error: "Please enter an intent first" });
      return;
    }

    set({ isGenerating: true, error: null });
    try {
      const testCases = await api.generateTestCases(intent, count);
      set({ testCases, isGenerating: false });
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
}));
