import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PromptEditor } from "@/components/training-ground/PromptEditor";
import { useTrainingStore } from "@/lib/store";

// Mock the store
vi.mock("@/lib/store", () => ({
  useTrainingStore: vi.fn(),
}));

describe("PromptEditor", () => {
  const mockStore = {
    intent: "",
    setIntent: vi.fn(),
    currentSystemPrompt: "",
    setCurrentSystemPrompt: vi.fn(),
    selectedModel: "gpt-4o",
    setSelectedModel: vi.fn(),
    generateCount: 50,
    setGenerateCount: vi.fn(),
    optimizerType: "bootstrap_fewshot",
    setOptimizerType: vi.fn(),
    hasGenerated: false,
    testCases: [],
    runs: [],
    promptVersions: [],
    activePromptVersionId: null,
    isGenerating: false,
    isRunning: false,
    isOptimizing: false,
    isSplit: false,
    generateTestCases: vi.fn(),
    runEvaluation: vi.fn(),
    optimizePrompt: vi.fn(),
    savePromptVersion: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useTrainingStore).mockReturnValue(mockStore);
  });

  describe("Initial State (before generation)", () => {
    it("should render Judge Intent input", () => {
      render(<PromptEditor />);
      expect(screen.getByLabelText("Judge Intent")).toBeInTheDocument();
    });

    it("should render Number to Generate input with default value of 50", () => {
      render(<PromptEditor />);
      const input = screen.getByLabelText("Number to Generate");
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue(50);
    });

    it("should render Model selector", () => {
      render(<PromptEditor />);
      // Select components don't use proper label associations
      expect(screen.getByText("Model")).toBeInTheDocument();
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("should render Generate Test Cases button", () => {
      render(<PromptEditor />);
      expect(screen.getByRole("button", { name: /generate test cases/i })).toBeInTheDocument();
    });

    it("should NOT render System Prompt textarea before generation", () => {
      render(<PromptEditor />);
      expect(screen.queryByLabelText("System Prompt")).not.toBeInTheDocument();
    });

    it("should NOT render Run Evaluation button before generation", () => {
      render(<PromptEditor />);
      expect(screen.queryByRole("button", { name: /run evaluation/i })).not.toBeInTheDocument();
    });

    it("should NOT render Optimize button before generation", () => {
      render(<PromptEditor />);
      expect(screen.queryByRole("button", { name: /optimize/i })).not.toBeInTheDocument();
    });
  });

  describe("After Generation", () => {
    const promptVersionId = "version-1";
    beforeEach(() => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        hasGenerated: true,
        currentSystemPrompt: "Generated system prompt",
        activePromptVersionId: promptVersionId,
        promptVersions: [
          {
            id: promptVersionId,
            version: 1,
            systemPrompt: "Generated system prompt",
            source: "generated",
            createdAt: new Date().toISOString(),
            parentVersionId: null,
          },
        ],
        testCases: [
          {
            id: "test-1",
            input_text: "Hello",
            expected_verdict: "PASS",
            reasoning: "Friendly",
            verified: false,
          },
        ],
      });
    });

    it("should render System Prompt textarea after generation", () => {
      render(<PromptEditor />);
      expect(screen.getByLabelText("System Prompt")).toBeInTheDocument();
    });

    it("should render Run Evaluation button after generation", () => {
      render(<PromptEditor />);
      expect(screen.getByRole("button", { name: /run evaluation/i })).toBeInTheDocument();
    });

    it("should render Optimize button after generation", () => {
      render(<PromptEditor />);
      expect(screen.getByRole("button", { name: /optimize/i })).toBeInTheDocument();
    });

    it("should display the generated system prompt", () => {
      render(<PromptEditor />);
      const textarea = screen.getByLabelText("System Prompt");
      expect(textarea).toHaveValue("Generated system prompt");
    });

    it("should render Save as New Version button", () => {
      render(<PromptEditor />);
      expect(screen.getByRole("button", { name: /save as new version/i })).toBeInTheDocument();
    });
  });

  describe("User Interactions", () => {
    it("should call setIntent when typing in intent field", () => {
      render(<PromptEditor />);
      const input = screen.getByLabelText("Judge Intent");
      fireEvent.change(input, { target: { value: "Detect spam" } });
      expect(mockStore.setIntent).toHaveBeenCalledWith("Detect spam");
    });

    it("should call setGenerateCount when changing number input", () => {
      render(<PromptEditor />);
      const input = screen.getByLabelText("Number to Generate");
      fireEvent.change(input, { target: { value: "25" } });
      expect(mockStore.setGenerateCount).toHaveBeenCalledWith(25);
    });

    it("should call generateTestCases when clicking generate button", () => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        intent: "Detect spam",
      });

      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /generate test cases/i });
      fireEvent.click(button);
      expect(mockStore.generateTestCases).toHaveBeenCalled();
    });

    it("should disable generate button when intent is empty", () => {
      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /generate test cases/i });
      expect(button).toBeDisabled();
    });

    it("should disable generate button when generating", () => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        intent: "Test",
        isGenerating: true,
      });

      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /generate test cases/i });
      expect(button).toBeDisabled();
    });
  });

  describe("Run Evaluation", () => {
    const promptVersionId = "version-1";
    beforeEach(() => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        hasGenerated: true,
        activePromptVersionId: promptVersionId,
        promptVersions: [
          {
            id: promptVersionId,
            version: 1,
            systemPrompt: "Test prompt",
            source: "generated",
            createdAt: new Date().toISOString(),
            parentVersionId: null,
          },
        ],
        testCases: [
          {
            id: "test-1",
            input_text: "Hello",
            expected_verdict: "PASS",
            reasoning: "Friendly",
            verified: false,
          },
        ],
      });
    });

    it("should call runEvaluation when clicking run button", () => {
      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /run evaluation/i });
      fireEvent.click(button);
      expect(mockStore.runEvaluation).toHaveBeenCalled();
    });

    it("should disable run button when running", () => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        hasGenerated: true,
        activePromptVersionId: promptVersionId,
        promptVersions: [
          {
            id: promptVersionId,
            version: 1,
            systemPrompt: "Test",
            source: "generated",
            createdAt: new Date().toISOString(),
            parentVersionId: null,
          },
        ],
        testCases: [{ id: "1", input_text: "", expected_verdict: "PASS", reasoning: "", verified: false }],
        isRunning: true,
      });

      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /run evaluation/i });
      expect(button).toBeDisabled();
    });

    it("should disable run button when no test cases", () => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        hasGenerated: true,
        activePromptVersionId: promptVersionId,
        promptVersions: [
          {
            id: promptVersionId,
            version: 1,
            systemPrompt: "Test",
            source: "generated",
            createdAt: new Date().toISOString(),
            parentVersionId: null,
          },
        ],
        testCases: [],
      });

      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /run evaluation/i });
      expect(button).toBeDisabled();
    });
  });

  describe("Optimize", () => {
    const promptVersionId = "version-1";

    it("should disable optimize button when accuracy is 100%", () => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        hasGenerated: true,
        activePromptVersionId: promptVersionId,
        promptVersions: [
          {
            id: promptVersionId,
            version: 1,
            systemPrompt: "Test",
            source: "generated",
            createdAt: new Date().toISOString(),
            parentVersionId: null,
          },
        ],
        testCases: [{ id: "1", input_text: "", expected_verdict: "PASS", reasoning: "", verified: false }],
        runs: [
          {
            id: "run-1",
            promptVersionId,
            modelName: "gpt-4o",
            createdAt: new Date().toISOString(),
            stats: {
              total: 1,
              passed: 1,
              failed: 0,
              errors: 0,
              accuracy: 100,
              cohen_kappa: 1.0,
              results: [],
            },
          },
        ],
      });

      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /optimize/i });
      expect(button).toBeDisabled();
    });

    it("should enable optimize button when accuracy is below 100%", () => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        hasGenerated: true,
        activePromptVersionId: promptVersionId,
        promptVersions: [
          {
            id: promptVersionId,
            version: 1,
            systemPrompt: "Test",
            source: "generated",
            createdAt: new Date().toISOString(),
            parentVersionId: null,
          },
        ],
        testCases: [{ id: "1", input_text: "", expected_verdict: "PASS", reasoning: "", verified: false }],
        runs: [
          {
            id: "run-1",
            promptVersionId,
            modelName: "gpt-4o",
            createdAt: new Date().toISOString(),
            stats: {
              total: 2,
              passed: 1,
              failed: 1,
              errors: 0,
              accuracy: 50,
              cohen_kappa: 0.5,
              results: [],
            },
          },
        ],
      });

      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /optimize/i });
      expect(button).not.toBeDisabled();
    });

    it("should call optimizePrompt when clicking optimize button", () => {
      vi.mocked(useTrainingStore).mockReturnValue({
        ...mockStore,
        hasGenerated: true,
        activePromptVersionId: promptVersionId,
        promptVersions: [
          {
            id: promptVersionId,
            version: 1,
            systemPrompt: "Test",
            source: "generated",
            createdAt: new Date().toISOString(),
            parentVersionId: null,
          },
        ],
        testCases: [{ id: "1", input_text: "", expected_verdict: "PASS", reasoning: "", verified: false }],
        runs: [
          {
            id: "run-1",
            promptVersionId,
            modelName: "gpt-4o",
            createdAt: new Date().toISOString(),
            stats: {
              total: 2,
              passed: 1,
              failed: 1,
              errors: 0,
              accuracy: 50,
              cohen_kappa: 0.5,
              results: [],
            },
          },
        ],
      });

      render(<PromptEditor />);
      const button = screen.getByRole("button", { name: /optimize/i });
      fireEvent.click(button);
      expect(mockStore.optimizePrompt).toHaveBeenCalled();
    });
  });
});
