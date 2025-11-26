import { TestCase, EvaluationResult, GenerateResponse, RunStats, OptimizeResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async generateTestCases(intent: string, count: number = 10): Promise<TestCase[]> {
    const response = await this.request<GenerateResponse>("/api/generate", {
      method: "POST",
      body: JSON.stringify({ intent, count }),
    });
    return response.test_cases;
  }

  async runEvaluation(
    systemPrompt: string,
    testCases: TestCase[],
    modelName: string
  ): Promise<RunStats> {
    return this.request<RunStats>("/api/run", {
      method: "POST",
      body: JSON.stringify({
        system_prompt: systemPrompt,
        test_cases: testCases,
        model_name: modelName,
      }),
    });
  }

  async optimizePrompt(
    currentPrompt: string,
    testCases: TestCase[],
    results: EvaluationResult[]
  ): Promise<OptimizeResponse> {
    return this.request<OptimizeResponse>("/api/optimize", {
      method: "POST",
      body: JSON.stringify({
        current_prompt: currentPrompt,
        test_cases: testCases,
        results: results,
      }),
    });
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health");
  }
}

export const api = new ApiClient();
