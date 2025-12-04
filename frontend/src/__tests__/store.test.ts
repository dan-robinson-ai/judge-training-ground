import { describe, it, expect, beforeEach, vi } from "vitest";
import { useTrainingStore } from "@/lib/store";
import { api } from "@/lib/api";

// Mock the API module
vi.mock("@/lib/api", () => ({
  api: {
    generateTestCases: vi.fn(),
    runEvaluation: vi.fn(),
    optimizePrompt: vi.fn(),
  },
}));

// Mock the persistence module
vi.mock("@/lib/persistence", () => ({
  storage: {
    getAllDatasets: vi.fn().mockResolvedValue([]),
    getDataset: vi.fn().mockResolvedValue(null),
    saveDataset: vi.fn().mockResolvedValue(undefined),
    deleteDataset: vi.fn().mockResolvedValue(undefined),
  },
}));

describe("TrainingStore", () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useTrainingStore.setState({
      // App-level UI state
      sidebarCollapsed: false,
      // Dataset collection state
      datasets: [],
      activeDatasetId: null,
      isLoadingDatasets: false,
      // Active dataset state
      intent: "",
      testCases: [],
      promptVersions: [],
      runs: [],
      activePromptVersionId: null,
      currentSystemPrompt: "",
      selectedModel: "gpt-4o",
      generateCount: 50,
      optimizerType: "bootstrap_fewshot",
      hasGenerated: false,
      isGenerating: false,
      isRunning: false,
      isOptimizing: false,
      isSplit: false,
      error: null,
      activeTab: "dataset",
    });
    vi.clearAllMocks();
  });

  describe("Initial State", () => {
    it("should have correct initial values", () => {
      const state = useTrainingStore.getState();
      expect(state.intent).toBe("");
      expect(state.currentSystemPrompt).toBe("");
      expect(state.testCases).toEqual([]);
      expect(state.runs).toEqual([]);
      expect(state.promptVersions).toEqual([]);
      expect(state.selectedModel).toBe("gpt-4o");
      expect(state.generateCount).toBe(50);
      expect(state.hasGenerated).toBe(false);
      expect(state.isGenerating).toBe(false);
      expect(state.isRunning).toBe(false);
      expect(state.isOptimizing).toBe(false);
      expect(state.error).toBeNull();
      expect(state.activeTab).toBe("dataset");
    });
  });

  describe("Setters", () => {
    it("should set intent", () => {
      useTrainingStore.getState().setIntent("Detect toxic messages");
      expect(useTrainingStore.getState().intent).toBe("Detect toxic messages");
    });

    it("should set current system prompt", () => {
      useTrainingStore.getState().setCurrentSystemPrompt("You are a judge...");
      expect(useTrainingStore.getState().currentSystemPrompt).toBe("You are a judge...");
    });

    it("should set selected model", () => {
      useTrainingStore.getState().setSelectedModel("claude-3-5-sonnet-20241022");
      expect(useTrainingStore.getState().selectedModel).toBe("claude-3-5-sonnet-20241022");
    });

    it("should set generate count", () => {
      useTrainingStore.getState().setGenerateCount(25);
      expect(useTrainingStore.getState().generateCount).toBe(25);
    });

    it("should set active tab", () => {
      useTrainingStore.getState().setActiveTab("history");
      expect(useTrainingStore.getState().activeTab).toBe("history");
    });

    it("should clear error", () => {
      useTrainingStore.setState({ error: "Some error" });
      useTrainingStore.getState().clearError();
      expect(useTrainingStore.getState().error).toBeNull();
    });
  });

  describe("Test Case Mutations", () => {
    beforeEach(() => {
      useTrainingStore.setState({
        testCases: [
          {
            id: "test-1",
            input_text: "Hello",
            expected_verdict: "PASS",
            reasoning: "Friendly",
            verified: false,
          },
          {
            id: "test-2",
            input_text: "Bad message",
            expected_verdict: "FAIL",
            reasoning: "Hostile",
            verified: false,
          },
        ],
      });
    });

    it("should update a test case", () => {
      useTrainingStore.getState().updateTestCase("test-1", { verified: true });
      const testCase = useTrainingStore.getState().testCases.find((tc) => tc.id === "test-1");
      expect(testCase?.verified).toBe(true);
    });

    it("should delete a test case", () => {
      useTrainingStore.getState().deleteTestCase("test-1");
      expect(useTrainingStore.getState().testCases).toHaveLength(1);
      expect(useTrainingStore.getState().testCases[0].id).toBe("test-2");
    });

    it("should add a test case", () => {
      const newTestCase = {
        id: "test-3",
        input_text: "New message",
        expected_verdict: "PASS" as const,
        reasoning: "New reasoning",
        verified: false,
      };
      useTrainingStore.getState().addTestCase(newTestCase);
      expect(useTrainingStore.getState().testCases).toHaveLength(3);
      expect(useTrainingStore.getState().testCases[2].id).toBe("test-3");
    });
  });

  describe("Async Actions", () => {
    describe("generateTestCases", () => {
      it("should set error if intent is empty", async () => {
        await useTrainingStore.getState().generateTestCases();
        expect(useTrainingStore.getState().error).toBe("Please enter an intent first");
      });

      it("should generate test cases successfully", async () => {
        const mockResponse = {
          test_cases: [
            {
              id: "gen-1",
              input_text: "Generated text",
              expected_verdict: "PASS" as const,
              reasoning: "Generated reasoning",
              verified: false,
            },
          ],
          system_prompt: "Generated system prompt",
        };

        vi.mocked(api.generateTestCases).mockResolvedValue(mockResponse);

        useTrainingStore.setState({
          intent: "Detect spam",
          generateCount: 10,
          selectedModel: "gpt-4o",
        });

        await useTrainingStore.getState().generateTestCases();

        expect(api.generateTestCases).toHaveBeenCalledWith("Detect spam", 10, "gpt-4o");
        expect(useTrainingStore.getState().testCases).toEqual(mockResponse.test_cases);
        expect(useTrainingStore.getState().currentSystemPrompt).toBe("Generated system prompt");
        expect(useTrainingStore.getState().promptVersions).toHaveLength(1);
        expect(useTrainingStore.getState().promptVersions[0].source).toBe("generated");
        expect(useTrainingStore.getState().hasGenerated).toBe(true);
        expect(useTrainingStore.getState().isGenerating).toBe(false);
      });

      it("should handle generation error", async () => {
        vi.mocked(api.generateTestCases).mockRejectedValue(new Error("API Error"));

        useTrainingStore.setState({ intent: "Test" });
        await useTrainingStore.getState().generateTestCases();

        expect(useTrainingStore.getState().error).toBe("API Error");
        expect(useTrainingStore.getState().isGenerating).toBe(false);
      });
    });

    describe("runEvaluation", () => {
      it("should set error if no test cases", async () => {
        await useTrainingStore.getState().runEvaluation();
        expect(useTrainingStore.getState().error).toBe("No test cases to evaluate");
      });

      it("should run evaluation successfully", async () => {
        const mockRunStats = {
          total: 1,
          passed: 1,
          failed: 0,
          errors: 0,
          accuracy: 100,
          cohen_kappa: 1.0,
          results: [
            {
              test_case_id: "test-1",
              actual_verdict: "PASS" as const,
              reasoning: "Good",
              correct: true,
            },
          ],
        };

        vi.mocked(api.runEvaluation).mockResolvedValue(mockRunStats);

        const promptVersionId = "version-1";
        useTrainingStore.setState({
          currentSystemPrompt: "You are a judge",
          testCases: [
            {
              id: "test-1",
              input_text: "Hello",
              expected_verdict: "PASS",
              reasoning: "Friendly",
              verified: false,
            },
          ],
          selectedModel: "gpt-4o",
          activePromptVersionId: promptVersionId,
          promptVersions: [
            {
              id: promptVersionId,
              version: 1,
              systemPrompt: "You are a judge",
              source: "manual",
              createdAt: new Date().toISOString(),
              parentVersionId: null,
            },
          ],
        });

        await useTrainingStore.getState().runEvaluation();

        expect(api.runEvaluation).toHaveBeenCalledWith(
          "You are a judge",
          expect.any(Array),
          "gpt-4o"
        );
        expect(useTrainingStore.getState().runs).toHaveLength(1);
        expect(useTrainingStore.getState().runs[0].stats).toEqual(mockRunStats);
        expect(useTrainingStore.getState().activeTab).toBe("history");
      });
    });

    describe("optimizePrompt", () => {
      it("should set error if no runs", async () => {
        useTrainingStore.setState({
          activePromptVersionId: "version-1",
          runs: [],
        });
        await useTrainingStore.getState().optimizePrompt();
        expect(useTrainingStore.getState().error).toBe("Run an evaluation first");
      });

      it("should optimize prompt successfully", async () => {
        const testCase = {
          id: "test-1",
          input_text: "Hello",
          expected_verdict: "PASS" as const,
          reasoning: "Friendly",
          verified: false,
        };

        const mockOptimizeResponse = {
          optimized_prompt: "Improved prompt",
          modification_notes: "Better handling",
          train_cases: [{ ...testCase, split: "train" as const }],
          test_cases: [],
        };

        vi.mocked(api.optimizePrompt).mockResolvedValue(mockOptimizeResponse);

        const promptVersionId = "version-1";
        useTrainingStore.setState({
          currentSystemPrompt: "Original prompt",
          testCases: [testCase],
          activePromptVersionId: promptVersionId,
          promptVersions: [
            {
              id: promptVersionId,
              version: 1,
              systemPrompt: "Original prompt",
              source: "manual",
              createdAt: new Date().toISOString(),
              parentVersionId: null,
            },
          ],
          runs: [
            {
              id: "run-1",
              promptVersionId: promptVersionId,
              modelName: "gpt-4o",
              createdAt: new Date().toISOString(),
              stats: {
                total: 1,
                passed: 0,
                failed: 1,
                errors: 0,
                accuracy: 0,
                cohen_kappa: 0,
                results: [
                  {
                    test_case_id: "test-1",
                    actual_verdict: "FAIL" as const,
                    reasoning: "Wrong",
                    correct: false,
                  },
                ],
              },
            },
          ],
        });

        await useTrainingStore.getState().optimizePrompt();

        expect(useTrainingStore.getState().currentSystemPrompt).toBe("Improved prompt");
        expect(useTrainingStore.getState().promptVersions).toHaveLength(2);
        expect(useTrainingStore.getState().promptVersions[1].source).toBe("optimized");
        expect(useTrainingStore.getState().isOptimizing).toBe(false);
        expect(useTrainingStore.getState().isSplit).toBe(true);
      });
    });
  });
});
