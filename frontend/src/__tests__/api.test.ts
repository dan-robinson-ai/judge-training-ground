import { describe, it, expect, beforeEach, vi } from "vitest";
import { api } from "@/lib/api";

describe("ApiClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("generateTestCases", () => {
    it("should call generate endpoint with correct parameters", async () => {
      const mockResponse = {
        test_cases: [
          {
            id: "test-1",
            input_text: "Hello",
            expected_verdict: "PASS",
            reasoning: "Friendly",
            verified: false,
          },
        ],
        system_prompt: "You are a judge...",
      };

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await api.generateTestCases("Detect spam", 25, "gpt-4o-mini");

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/generate",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ intent: "Detect spam", count: 25, model: "gpt-4o-mini" }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it("should use default values", async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ test_cases: [], system_prompt: "" }),
      } as Response);

      await api.generateTestCases("Test");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ intent: "Test", count: 50, model: "gpt-4o" }),
        })
      );
    });

    it("should throw error on failed request", async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Invalid request" }),
      } as Response);

      await expect(api.generateTestCases("Test")).rejects.toThrow("Invalid request");
    });
  });

  describe("runEvaluation", () => {
    it("should call run endpoint with correct parameters", async () => {
      const mockResponse = {
        total: 1,
        passed: 1,
        failed: 0,
        errors: 0,
        accuracy: 100,
        results: [],
      };

      const testCases = [
        {
          id: "test-1",
          input_text: "Hello",
          expected_verdict: "PASS" as const,
          reasoning: "Friendly",
          verified: false,
        },
      ];

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await api.runEvaluation("System prompt", testCases, "gpt-4o");

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/run",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            system_prompt: "System prompt",
            test_cases: testCases,
            model_name: "gpt-4o",
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("optimizePrompt", () => {
    it("should call optimize endpoint with correct parameters", async () => {
      const mockResponse = {
        optimized_prompt: "Better prompt",
        modification_notes: "Improved",
      };

      const testCases = [
        {
          id: "test-1",
          input_text: "Hello",
          expected_verdict: "PASS" as const,
          reasoning: "Friendly",
          verified: false,
        },
      ];

      const results = [
        {
          test_case_id: "test-1",
          actual_verdict: "FAIL" as const,
          reasoning: "Wrong",
          correct: false,
        },
      ];

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await api.optimizePrompt("Current prompt", testCases, results);

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/optimize",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            current_prompt: "Current prompt",
            test_cases: testCases,
            results: results,
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("healthCheck", () => {
    it("should call health endpoint", async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: "healthy" }),
      } as Response);

      const result = await api.healthCheck();

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/health",
        expect.objectContaining({
          headers: { "Content-Type": "application/json" },
        })
      );
      expect(result).toEqual({ status: "healthy" });
    });
  });

  describe("Error Handling", () => {
    it("should handle network errors", async () => {
      vi.mocked(global.fetch).mockRejectedValue(new Error("Network error"));

      await expect(api.healthCheck()).rejects.toThrow("Network error");
    });

    it("should handle JSON parse errors in error response", async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("Invalid JSON")),
      } as Response);

      await expect(api.healthCheck()).rejects.toThrow("HTTP 500");
    });
  });
});
