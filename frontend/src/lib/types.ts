export interface TestCase {
  id: string;
  input_text: string;
  expected_verdict: "PASS" | "FAIL";
  reasoning: string;
  verified: boolean;
}

export interface EvaluationResult {
  test_case_id: string;
  actual_verdict: "PASS" | "FAIL" | "ERROR";
  reasoning: string;
  correct: boolean;
}

export interface RunStats {
  total: number;
  passed: number;
  failed: number;
  errors: number;
  accuracy: number;
  results: EvaluationResult[];
}

export interface GenerateResponse {
  test_cases: TestCase[];
}

export interface OptimizeResponse {
  optimized_prompt: string;
  modification_notes: string;
}

export type ModelOption = {
  value: string;
  label: string;
  provider: string;
};

export const AVAILABLE_MODELS: ModelOption[] = [
  { value: "gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini", provider: "OpenAI" },
  { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { value: "claude-3-5-haiku-20241022", label: "Claude 3.5 Haiku", provider: "Anthropic" },
];
